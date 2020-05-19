function init() {
	setInterval(dateandtime, 1000);
}

function dateandtime() {
    var today = new Date();
    var h = today.getHours();
    var m = today.getMinutes();
    var s = today.getSeconds();
    m = checkTime(m);
    s = checkTime(s);
//     document.getElementById('time').innerHTML = today.toLocaleTimeString();
//     document.getElementById('date').innerHTML = today.toDateString();
// }

function checkTime(i) {
    if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
    return i;
}