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

function invertButton(button, mac, video, barRow) {
    video.saved = !video.saved;
    buttonDiv = button.parentElement;
    var newButton = createButton(buttonDiv, video.saved);
    buttonDiv.removeChild(button);
    addButtonListener(newButton, mac, video, barRow);
    updateBarRow(barRow, video, mac);
}

function updateBarRow(barRow, video, mac) {
    if (video.saved) {
        createSlider(barRow, video, mac);
    } else {
        createDownloadBar(barRow);
    }
}

function updateProgressBar(barRow, button, mac, video) {
    const UPDATE_INTERVAL = 666;
    const BARROW_UPDATE_DELAY = 2000;
    barRow.style.display = "block";
    var t = setInterval(function () {
        var progressRequest = new XMLHttpRequest();
        var progressUrl = "/songs/" + encodeURIComponent(video.id);
        progressRequest.onload = function () {
            var response = JSON.parse(progressRequest.responseText);
            var childDivs = barRow.getElementsByTagName('div');
            var loadingText = childDivs[1];
            var progressBar = childDivs[2].firstChild.firstChild;
            var progress = parseInt(response.progress, loadingText);
            if (loadingText.innerHTML.length === 10) {
                loadingText.innerHTML = "Loading";
            } else {
                loadingText.innerHTML += '.';
            }
            progressBar.innerHTML = progress + "%";
            progressBar.style.width = progress + "%";
            if (progress === 100) {
                clearInterval(t);
                loadingText.innerHTML = "Success!";
                progressBar.classList.remove("active");
                setTimeout(function () {
                    invertButton(button, mac, video, barRow);
                }, BARROW_UPDATE_DELAY);
            }
        };
        progressRequest.open("GET", progressUrl);
        progressRequest.send();
    }, UPDATE_INTERVAL);
}

function addButtonListener(button, mac, video, barRow) {
    button.addEventListener("click", function (e) {
        this.disabled = true;
        var request = new XMLHttpRequest();
        var url = "/devices/" + encodeURIComponent(mac) + "/songs/" + encodeURIComponent(video.id);
        if (!video.saved) {
            request.open("PUT", url);
            updateProgressBar(barRow, button, mac, video);
        } else {
            request.onload = function () {
                invertButton(button, mac, video, barRow);
            };
            request.open("DELETE", url);
        }
        request.send();
    });
}

function createSlider(barRow, video, mac) {
    barRow.innerHTML = "";
    addCol(barRow, 1, 2);
    var text = addCol(barRow, 3, 1);
    text.innerHTML = "Start: " + video.savedStart + "s";
    var sliderCol = addCol(barRow, 7, 7);
    addCol(barRow, 1, 2);
    var input = document.createElement('input');
    input.type = "text";
    input.setAttribute("data-slider-min", '0');
    input.setAttribute("data-slider-max", "" + video.duration);
    input.setAttribute("data-slider-value", "" + video.savedStart);
    input.id = "slider-" + video.id;
    sliderCol.appendChild(input);
    var slider = new Slider('#'+input.id, {
        formatter: function (value) {
            text.innerHTML = "Start: " + value + "s";
            return value;
        }
    });
    slider.on('slideStop', function (newValue) {
        var request = new XMLHttpRequest();
        var url = "/devices/"+encodeURIComponent(mac)+"/songs/"+encodeURIComponent(video.id);
        request.open("POST", url);
        request.setRequestHeader('Content-Type', 'application/json');
        request.send(JSON.stringify({'start': newValue}));
    });
    barRow.style.display = "block";
}

function createDownloadBar(barRow) {
    barRow.innerHTML = "";
    addCol(barRow, 1, 2);
    var barRowText = addCol(barRow, 4, 1);
    var progressBarCol = addCol(barRow, 6, 7);
    addCol(barRow, 1, 2);
    barRowText.innerHTML = "Loading";
    var progressDiv = document.createElement('div');
    progressBarCol.appendChild(progressDiv);
    progressDiv.className = "progress";
    var progressBar = document.createElement('div');
    progressDiv.appendChild(progressBar);
    progressBar.className = "progress-bar progress-bar-striped progress-bar-success active";
    progressBar.setAttribute('style', "width: 0; min-width: 2em");
    progressBar.innerHTML = "0%";
    barRow.style.display = "none";
}

function createRow(container, video, mac) {
    var row = addRow(container);
    addCol(row, 1, 2);
    var videoCol = addCol(row, 8, 5);
    videoCol.insertAdjacentHTML("beforeend", `<div class="embed-responsive embed-responsive-16by9">
                                                <iframe class="embed-responsive-item" src="//www.youtube.com/embed/` + video.id + `?rel=0"></iframe>
                                              </div>`);
    var btnCol = addCol(row, 2, 3);
    var button = createButton(btnCol, video.saved);
    var barRow = addRow(container, false);
    if (video.saved) {
        createSlider(barRow, video, mac);
    } else {
        createDownloadBar(barRow);
    }
    addButtonListener(button, mac, video, barRow);
    addCol(row, 1, 2);
}

function makeVideoRequest() {
    var request = new XMLHttpRequest();
    request.onload = function () {
        var response = JSON.parse(request.responseText);
        var videos = response.videos;
        var mac = response.mac;
        var div = document.getElementById('search-result');
        div.innerHTML = '';
        for (var i = 0; i < videos.length; i++) {
            createRow(div, videos[i], mac)
        }
    };
    return request;
}

function requestVideoSearch() {
    var button = document.getElementById("searchBtn");
    button.addEventListener("click", function (e) {
        e.preventDefault();
        var key = document.getElementById("searchKey").value;
        var request = makeVideoRequest();
        request.open("GET", "/search?k=" + encodeURIComponent(key), true);
        request.send();
    });
}

function requestUserVideo() {
    var request = makeVideoRequest();
    request.open("GET", "/search", true);
    request.send();
}

addEventListener("DOMContentLoaded", function () {
    var isSettings = window.location.pathname.includes('settings');
    if (isSettings) {
        requestUserVideo();
    } else {
        requestVideoSearch();
    }
}, true);