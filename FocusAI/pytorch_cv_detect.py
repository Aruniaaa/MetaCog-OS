import cv2
import numpy as np
import threading
import time
import requests
import logging
from collections import deque
import torch
import os
import gdown

logger = logging.getLogger(__name__)


class PhoneDetector:
    def __init__(self):
        self.model = None
        self.is_running = False
        self.detection_thread = None
        self.camera = None
        self.user_id = None
        self.last_detection_time = 0
        self.detection_cooldown = 2
        self.confidence = 0
        self.frame_count = 0
        self.start_time = time.time()

        self.confidence_threshold = 0.6
        self.required_detections = 3
        self.sustained_duration = 2.0

        self.confidence_history = deque(maxlen=10)
        self.high_confidence_count = 0
        self.high_confidence_start_time = None
        self.detection_buffer = deque(maxlen=self.required_detections)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self, model_path, file_id):
        try:
            if not os.path.exists(model_path):
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                url = f"https://drive.google.com/uc?id={file_id}"
                print("Downloading AI model...")
                gdown.download(url, model_path, quiet=False)
                print("AI model downloaded!")
            else:
                print("Model file already exists, loading...")

            self.model = torch.load(model_path, weights_only=False, map_location=self.device)
            self.model.eval()
            return True

        except Exception as e:
            print(f"AN EXCEPTION OCCURED WHILE LOADING THE MODEL : {e}")
            logger.error(f"Failed to load model: {e}")
            return False

    def preprocess_frame(self, frame):

        resized = cv2.resize(frame, (224, 224))

        rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        tensor = torch.from_numpy(rgb_frame).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        tensor = tensor.to(self.device)

        mean = torch.tensor([0.485, 0.456, 0.406], device=self.device).view(1,3,1,1)
        std = torch.tensor([0.229, 0.224, 0.225], device=self.device).view(1,3,1,1)
        tensor = (tensor - mean) / std

        return tensor

    def should_trigger_detection(self):

        current_time = time.time()

        high_conf_count = sum(1 for conf in self.detection_buffer if conf >= self.confidence_threshold)

        avg_confidence = np.mean(list(self.detection_buffer)) if self.detection_buffer else 0

        debug_info = {
            'high_conf_count': high_conf_count,
            'required_detections': self.required_detections,
            'duration_sustained': current_time - self.high_confidence_start_time if self.high_confidence_start_time else 0,
            'avg_confidence': avg_confidence,
            'buffer_size': len(self.detection_buffer),
            'buffer_contents': list(self.detection_buffer)
        }

        if avg_confidence >= self.confidence_threshold:
            if self.high_confidence_start_time is None:
                self.high_confidence_start_time = current_time
        else:
            self.high_confidence_start_time = None

        sustained = (
                self.high_confidence_start_time and
                (current_time - self.high_confidence_start_time) >= self.sustained_duration
        )

        should_trigger = (high_conf_count >= self.required_detections and sustained)
        should_trigger = bool(should_trigger)

        return should_trigger, debug_info

    def detect_phone_in_frame(self, frame):

        if self.model is None:
            print("MODEL IS NONE!")
            return False, {}

        try:
            processed_frame = self.preprocess_frame(frame)

            with torch.no_grad():
                predictions = self.model(processed_frame)

            probs  = torch.sigmoid(predictions)

            prob = probs.item()

            self.confidence = prob
            self.frame_count += 1

            self.confidence_history.append(prob)
            self.detection_buffer.append(prob)

            current_time = time.time()

            if self.confidence >= self.confidence_threshold:
                if self.high_confidence_start_time is None:
                    self.high_confidence_start_time = current_time
                self.high_confidence_count += 1

            else:
                if self.high_confidence_start_time is not None:
                    self.high_confidence_start_time = None
                    self.high_confidence_count = 0

            should_trigger, debug_info = self.should_trigger_detection()

            return should_trigger, debug_info

        except Exception as e:
            print(f"Exception while inference: {e}")
            logger.error(f"Error during phone detection: {e}")
            return False, {}

    def reset_detection_state(self):
        self.high_confidence_start_time = None
        self.high_confidence_count = 0
        self.detection_buffer.clear()

    def get_detection_stats(self):

        current_time = time.time()

        return {
            'confidence_threshold': self.confidence_threshold,
            'required_detections': self.required_detections,
            'current_confidence': self.confidence,
            'confidence_history': list(self.confidence_history),
            'high_confidence_count': self.high_confidence_count,
            'sustained_duration': current_time - self.high_confidence_start_time if self.high_confidence_start_time else 0,
            'detection_buffer': list(self.detection_buffer),
            'avg_recent_confidence': np.mean(list(self.detection_buffer)) if self.detection_buffer else 0,
            'is_tracking_sustained': self.high_confidence_start_time is not None
        }

    def detection_loop(self):

        logger.info("Starting enhanced phone detection loop")

        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("CAMERA FAILED TO OPEN")

                return

            ret, test_frame = self.camera.read()
            if not ret or test_frame is None:
                print("CAMERA READ FAILED")

                self.camera.release()
                return
            logger.info("Camera opened successfully")

        except Exception as e:
            print(f"CAMERA EXCEPTION: {e}")

            return

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 10)

        frame_skip = 3
        frame_count = 0
        consecutive_failures = 0

        while self.is_running:
            ret, frame = self.camera.read()
            if not ret or frame is None:
                consecutive_failures += 1
                if consecutive_failures > 10:
                    break
                time.sleep(0.1)
                continue

            consecutive_failures = 0
            frame_count += 1

            if frame_count % frame_skip != 0:
                continue

            try:
                should_trigger, debug_info = self.detect_phone_in_frame(frame)

                if should_trigger:

                    logger.info("Sustained phone detection confirmed!")
                else:
                    stats = self.get_detection_stats()

            except Exception as e:
                print(f" DETECTION ERROR: {e}")
                logger.error(f"Error in detection loop: {e}")

            time.sleep(0.1)

        if self.camera:
            self.camera.release()
        logger.info("Enhanced phone detection loop stopped")

    def start_detection(self, user_id):

        if self.is_running:
            logger.warning("Detection already running")
            return False

        if self.model is None:
            logger.error("Model not loaded - cannot start detection")
            return False

        self.user_id = user_id
        self.is_running = True

        self.reset_detection_state()
        self.confidence_history.clear()

        self.detection_thread = threading.Thread(target=self.detection_loop)
        self.detection_thread.daemon = True
        self.detection_thread.start()

        logger.info(f"Enhanced phone detection started for user {user_id}")
        return True

    def stop_detection(self):

        if not self.is_running:
            return

        logger.info("Stopping enhanced phone detection...")
        self.is_running = False

        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=3.0)
            if self.detection_thread.is_alive():
                logger.warning("Detection thread did not stop gracefully")

        self.reset_detection_state()
        self.confidence_history.clear()
        self.user_id = None
        logger.info("Enhanced phone detection stopped")


phone_detector = PhoneDetector()
phone_detector.load_model('FocusAI/cnn-models/pytorch_model.pt', "15MspUrBVWKi4Wsh5JHRsEpWIMrtX-D28")