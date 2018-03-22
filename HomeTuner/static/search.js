function addRow(container, alignCenter = true) {
    var row = document.createElement('div');
    row.setAttribute('class', 'row');
    if (alignCenter) {
        row.setAttribute("style", "margin-top: 20px; display: flex;align-items: center");
    } else {
        row.setAttribute("style", "margin-top: 20px;");
    }
    container.appendChild(row);
    return row;
}

function addCol(row, xs, md) {
    var col = document.createElement('div');
    col.setAttribute('class', 'col-xs-' + xs + ' col-md-' + md);
    row.appendChild(col);
    return col;
}

function createButton(col, isSaved) {
    var button = document.createElement('button');
    col.appendChild(button);
    button.type = "submit";
    if (!isSaved) {
        button.setAttribute('class', 'btn btn-success center-block');
        button.insertAdjacentHTML("beforeend", 'Add <span class="glyphicon glyphicon-plus"></span>');
    } else {
        button.setAttribute('class', 'btn btn-danger center-block');
        button.insertAdjacentHTML("beforeend", 'Remove <span class="glyphicon glyphicon-minus"></span>');
    }
    return button;
}

function invertButton(button, mac, videoId, isSaved, row, progressBar, loadingText) {
    buttonDiv = button.parentElement;
    var newButton = createButton(buttonDiv, !isSaved);
    buttonDiv.removeChild(button);
    addButtonListener(newButton, mac, videoId, !isSaved, row, progressBar, loadingText);
}

function addButtonListener(button, mac, videoId, isSaved, row, progressBar, loadingText) {
    button.addEventListener("click", function (e) {
        var request = new XMLHttpRequest();
        var url = "/devices/" + encodeURIComponent(mac) + "/songs/" + encodeURIComponent(videoId);
        if (!isSaved) {
            request.onload = function () {
            };
            request.open("PUT", url);
            /* Progress bar update */
            const UPDATE_INTERVAL = 666;
            row.style.display = "block";
            var t = setInterval(function () {
                var progressRequest = new XMLHttpRequest();
                var progressUrl = "/songs/" + encodeURIComponent(videoId);
                progressRequest.onload = function () {
                    var response = JSON.parse(progressRequest.responseText);
                    var progress = parseInt(response.progress, loadingText);
                    if (loadingText.innerHTML.length === 10) {
                        loadingText.innerHTML = "Loading";
                    } else {
                        loadingText.innerHTML += '.';
                    }
                    progressBar.innerHTML = progress + "%";
                    progressBar.style.width = progress + "%";  // don't know why bar won't fill at 100%..
                    if (progress === 100) {
                        clearInterval(t);
                        loadingText.innerHTML = "Success!";
                        progressBar.classList.remove("active");
                        setTimeout(function () {
                            row.style.display = "none";
                        }, 2000);
                        invertButton(button, mac, videoId, isSaved, row, progressBar, loadingText);
                    }
                };
                progressRequest.open("GET", progressUrl);
                progressRequest.send();
            }, UPDATE_INTERVAL);
        } else {
            request.onload = function () {
                invertButton(button, mac, videoId, isSaved, row, progressBar, loadingText);
            };
            request.open("DELETE", url);
        }
        request.send();
    });
}

function createRow(container, videoId, isSaved, mac) {
    var row = addRow(container);
    addCol(row, 1, 2);
    var videoCol = addCol(row, 8, 5);
    videoCol.insertAdjacentHTML("beforeend", `<div class="embed-responsive embed-responsive-16by9">
                                                <iframe class="embed-responsive-item" src="//www.youtube.com/embed/` + videoId + `?rel=0"></iframe>
                                              </div>`);
    var btnCol = addCol(row, 2, 3);
    var button = createButton(btnCol, isSaved);
    var progressBarRow = addRow(container, false);
    addCol(progressBarRow, 1, 2);
    var loadingText = addCol(progressBarRow, 4, 1);
    var progressBarCol = addCol(progressBarRow, 6, 7);
    addCol(progressBarRow, 1, 2);
    loadingText.innerHTML = "Loading";
    var progressDiv = document.createElement('div');
    progressBarCol.appendChild(progressDiv);
    progressDiv.className = "progress";
    var progressBar = document.createElement('div');
    progressDiv.appendChild(progressBar);
    progressBar.className = "progress-bar progress-bar-striped progress-bar-success active";
    progressBar.setAttribute('style', "width: 0; min-width: 2em");
    progressBar.innerHTML = "0%";
    progressBarRow.style.display = "none";
    addButtonListener(button, mac, videoId, isSaved, progressBarRow, progressBar, loadingText);
    addCol(row, 1, 2);
}

addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("searchBtn");
    button.addEventListener("click", function (e) {
        e.preventDefault();
        var key = document.getElementById("searchKey").value;
        var request = new XMLHttpRequest();
        request.onload = function () {
            var response = JSON.parse(request.responseText);
            var videos = response.videos;
            var mac = response.mac;
            var div = document.getElementById('search-result');
            div.innerHTML = '';
            for (var i = 0; i < videos.length; i++) {
                createRow(div, videos[i].id, videos[i].saved, mac)
            }
        };
        request.open("GET", "/search?k=" + encodeURIComponent(key), true);
        request.send();
    });
}, true);