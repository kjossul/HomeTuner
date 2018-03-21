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
            var ul = document.getElementById('search-result');
            ul.innerHTML = '';
            for (var i = 0; i < videos.length; i++) {
                if (!videos[i].saved) {
                    var button = `<button class="btn btn-success center-block" type="submit" id="` + videos[i].id + `">
                                    Add <span class="glyphicon glyphicon-plus"></span>
                                    </button>`;
                } else {
                    var button = `<button class="btn btn-danger center-block" type="submit" id="` + videos[i].id + `">
                                    Remove <span class="glyphicon glyphicon-minus"></span>
                                    </button>`;
                }
                var html = `<div class="row" style="margin-top: 20px; display: flex;align-items: center">
                                <div class="col-xs-1 col-md-2"></div>
                                <div class="col-xs-8 col-md-5">
                                    <div class="embed-responsive embed-responsive-16by9">
                                        <iframe class="embed-responsive-item" src="//www.youtube.com/embed/` + videos[i].id + `?rel=0"></iframe>
                                    </div>
                                </div>
                                <div class="col-xs-2 col-md-3">` + button + `</div>
                                <div class="col-xs-1 col-md-2"></div>
                            </div>`;
                ul.insertAdjacentHTML("beforeend", html);
            }
            var addButtons = document.getElementsByClassName('btn-success');
            for (var i = 0; i < addButtons.length; i++) {
                addButtons[i].addEventListener("click", function (e) {
                    var addSongRequest = new XMLHttpRequest();
                    addSongRequest.onload = function () {
                    };
                    var url = "/devices/" + encodeURIComponent(mac) + "/songs/" + encodeURIComponent(this.id);
                    addSongRequest.open("PUT", url);
                    addSongRequest.send();
                });
            }
            var removeButtons = document.getElementsByClassName('btn-danger');
            for (var i = 0; i < removeButtons.length; i++) {
                removeButtons[i].addEventListener("click", function (e) {
                    var removeSongRequest = new XMLHttpRequest();
                    removeSongRequest.onload = function () {
                    };
                    var url = "/devices/" + encodeURIComponent(mac) + "/songs/" + encodeURIComponent(this.id);
                    removeSongRequest.open("DELETE", url);
                    removeSongRequest.send();
                });
            }
        };
        request.open("GET", "/search?k=" + encodeURIComponent(key), true);
        request.send();
    });
}, true);