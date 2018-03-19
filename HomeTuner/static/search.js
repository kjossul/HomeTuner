addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("searchBtn");
    button.addEventListener("click", function (e) {
        e.preventDefault();
        var key = document.getElementById("searchKey").value;
        var request = new XMLHttpRequest();
        request.onload = function () {
            console.log(request.responseText);
            var response = JSON.parse(request.responseText);
            var ul = document.getElementById('search-result');
            ul.innerHTML = '';
            for (var i = 0; i < response.length; i++) {
                console.log(i, response[i]);
                var html = `<li class="media">
                                <div class="media-left media-middle">
                                  <a href="/video?v=`+response[i]['id']+`">
                                    <img class="media-object" src="` + response[i]['thumbnail'] + `">
                                  </a>
                                </div>
                                <div class="media-body">
                                  <h4 class="media-heading">` + response[i]['title'] + `</h4>
                                </div>
                            </li>`;
                ul.insertAdjacentHTML("beforeend", html);
            }
        };
        // We point the request at the appropriate command
        request.open("GET", "/search?k=" + encodeURIComponent(key), true);
        // and then we send it off
        request.send();
    });
}, true);