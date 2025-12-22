document.addEventListener('DOMContentLoaded', function() {

    const weekday = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const d = new Date();
    const day = weekday[d.getDay()];
    const shouldGenerateNew = day === 'Sunday';

    const sectionMap = {
        "Suggestions & Feedback": 'suggestions_and_feedback',
        "Tips & Trick": 'tips_and_tricks',
        "Recommended Resources": 'recommended_resources',
        "Suggested Priorities for Next Weeks": 'suggested_priorities',
        "Pending Tasks & How to get them dones": 'pending_tasks' 
    };

    function populateList(elementId, dataArray, emptyMessage) {
        const targetElement = document.getElementById(elementId);

        if (!targetElement) {
            console.error(`Target element with ID "${elementId}" not found.`);
            return;
        }

        if (dataArray && dataArray.length > 0) {
            dataArray.forEach(itemText => {
                const li_node = document.createElement("li"); 
                const textnode = document.createTextNode(itemText);
                li_node.appendChild(textnode);
                targetElement.appendChild(li_node);
            });
        } else {
            const li_node = document.createElement("li");
            const textnode = document.createTextNode(emptyMessage);
            li_node.classList.add('empty-message');
            li_node.appendChild(textnode);
            targetElement.appendChild(li_node);
        }
    }



    console.log("About to make the fetch req!")
    fetch(`${MAKE_REPORT_URL}?generate_new=${shouldGenerateNew}`)
    .then(res => res.json())
    .then(data => {
        console.log(data);

        if (data)
        {
            populateList(
                sectionMap["Suggestions & Feedback"],
                data.report["Suggestions & Feedback"],
                "No new feedback available."
            );

            populateList(
                sectionMap["Tips & Trick"],
                data.report["Tips & Trick"],
                "No tips available today."
            );

            populateList(
                sectionMap["Recommended Resources"],
                data.report["Recommended Resources"],
                "No resources currently recommended."
            );

            populateList(
                sectionMap["Suggested Priorities for Next Weeks"],
                data.report["Suggested Priorities for Next Weeks"],
                "No new priorities suggested."
            );
            
            populateList(
                sectionMap["Pending Tasks & How to get them dones"],
                data.report["Pending Tasks & How to get them dones"],
                "Nothing to see here!"
            );
        }

    })
    .catch(err => {
        console.error("Error fetching or processing report data:", err);
    });

});