if (Notification.permission != "granted")
{
    Notification.requestPermission();
}

document.addEventListener('DOMContentLoaded', () => {

    const topRight = document.getElementById('top-right');
    const logged_in = document.getElementById('logged-in');
    const username = logged_in.querySelector("strong").textContent;


    if (topRight.contains(logged_in) && Notification.permission == "granted")
    {
        fetch("get_tasks")
        .then(res => res.json())
        .then (data => {
            const amount = data.amount;
            if (amount >= 1 && (localStorage.getItem("tasks") != amount.toString()))
            {
              const notif = new Notification("Incomplete Tasks!", {
                body: `${username}, you have ${amount} incomplete tasks. How about we aim to finish those today?`
              });
              localStorage.setItem("tasks", amount);

            };

        })
        .catch(e => {
            alert(`Oops, an error occurred: ${e}!`)
        })
    }

});


