let notifyRef;
function getCurrentDate() {
    let newDate = new Date();
    let date = newDate.toLocaleDateString("es-PE", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    });
    return date;
}

function getCurrentTime() {
    let today = new Date();
    let time = today.toLocaleTimeString("es-PE", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
    return time;
}



