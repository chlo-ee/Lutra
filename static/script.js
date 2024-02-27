class Animator {
    constructor() {
        this.msScheduling = 15
        this.tickPercentageIncrement = 2
        this.percentageTarget = 100
        this.percentageCurrent = 0
        this.lightingCycle = 0
        this.boxShadowX = "0"
        this.boxShadowS = "0"
        this.boxShadowY = "20px"
        this.boxShadowC = "#3FB5A0"
        this.running = false
        this.typeText = ""
        this.typeTextLetter = 0
        this.typingCycle = 0
    }

    start() {
        if (this.running) {
            console.error("Animator is already running.")
        } else {
            this.running = true
            window.setTimeout(() => {this.tick()}, 0)
        }
    }

    stop() {
        this.running = false
    }

    animate() {
        this.tickPercentage()
        this.tickLighting()
        this.tickShowBoxShadow()
        this.tickTypeText()
    }

    tick() {
        if (this.running) {
            window.setTimeout(() => {this.tick()}, this.msScheduling)
            this.lightingCycle ++
            this.animate()
        }
    }

    toDualDigitsHexStr(n) {
        var s = n.toString(16)
        if (s.length === 1) s = "0" + s
        return s
    }

    tickLighting() {
        this.boxShadowY = "5px"//Math.round(Math.abs(((this.lightingCycle / 80) % 5) - 2.5) + 2.5) + "px"
        this.boxShadowS = Math.round(Math.abs(((this.lightingCycle % 400) - 200) / 40)) + 5 + "px"

        var r = 0x3F
        var g = 0xB5
        var b = 0xA0

        r = Math.round((0.6 * r) * (Math.abs(((this.lightingCycle) % 400) - 200) / 320) + (r - (0.6 * r)))
        g = Math.round((0.6 * g) * (Math.abs(((this.lightingCycle) % 400) - 200) / 320) + (g - (0.6 * g)))
        b = Math.round((0.6 * b) * (Math.abs(((this.lightingCycle) % 400) - 200) / 320) + (b - (0.6 * b)))

        this.boxShadowC = "#" + this.toDualDigitsHexStr(r) + this.toDualDigitsHexStr(g) + this.toDualDigitsHexStr(b)
    }

    tickPercentage() {
        if (this.percentageTarget > this.percentageCurrent) {
            this.percentageCurrent += this.tickPercentageIncrement
        }
        else if (this.percentageTarget < this.percentageCurrent) {
            this.percentageCurrent = this.percentageTarget
        }
        this.showPercentage(this.percentageCurrent)
    }

    tickShowBoxShadow() {
        head.style.boxShadow = this.boxShadowX + " " + this.boxShadowY + " " + this.boxShadowS + " " + this.boxShadowC
    }

    tickTypeText() {
        if (this.lightingCycle % 5 !== 0) return

        let element = document.getElementById("content-code")
        if (!element) return
        if (element.innerText.length < this.typeText.length) {
            this.typeTextLetter++
            element.innerText = this.typeText.slice(0, this.typeTextLetter)
            element.scrollTop = 500000000
        }
    }

    showPercentage(percentage) {
        let head = document.getElementById("head")
        let width = head.clientWidth
        let pWidth = width - Math.round(width * (percentage / 100))
        this.boxShadowX = -pWidth + "px"
    }

    setPercentage(percentage) {
        this.percentageTarget = percentage
        this.animate()
    }
}

let animator = new Animator()
animator.start()

let apiBase = '/api/v1/'
function getApiRoute(functionName, args=null) {
    var route = apiBase + functionName
    if (args) {
        for (let arg of args) {
            route += '/' + arg
        }
    }
    return route
}

var map = null
let trackers = {}

fetch("static/script.js")
    .then((response) => response.text())
    .then((text) => animator.typeText = text)

async function performGetRequestWithFeedback(url, feedback=true, reload_on_401=true) {
    if (feedback) {
        animator.setPercentage(0)
    }

    let promise = fetch(url)
    promise.then(() => {
        if (feedback) {
            animator.setPercentage(100)
        }
    })
    promise.then((response) => {
        if (reload_on_401 && response.status === 401) {
            jwt = null
            logout()
        }
    })
    return promise
}

async function performPostWithFeedback(url, data) {
    animator.setPercentage(0)
    headers = {
        "Content-Type": "application/json",
    }

    let promise = fetch(url, {
        method: "POST",
        mode: "cors",
        cache: "no-cache",
        credentials: "same-origin",
        headers: headers,
        body: JSON.stringify(data)
    })
    promise.then(() => {animator.setPercentage(100)})
    return promise
}

function updateTrack(trackerId) {
    return performGetRequestWithFeedback(getApiRoute('track', [trackerId]))
        .then((response) => response.json())
        .then((json) => {
            track = Array.from(json, (_) => [_["lng"], _["lat"]])
            let sourceData = {
                'type': 'Feature',
                'properties': {},
                'geometry': {
                    'type': 'LineString',
                    'coordinates': track
                }
            }
            var source = map.getSource('route_' + trackerId)
            if (source) {
                source.setData(sourceData)
            } else {
                map.addSource('route_' + trackerId, {
                    'type': 'geojson',
                    'data': sourceData
                })
            }
        })
}

function toggleTrack(trackerId) {
    let toggleA = document.getElementById('map-popup-track-toggle-' + trackerId)
    if (toggleA.classList.contains('inactive')) {
        updateTrack(trackerId).then(() => {
            map.addLayer({
                'id': 'route_' + trackerId,
                'type': 'line',
                'source': 'route_' + trackerId,
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': '#3FB5A0',
                    'line-width': 4
                }
            })
        })
    } else {
        map.removeLayer('route_' + trackerId)
        map.removeSource('route_' + trackerId)
    }

    toggleA.classList.toggle('inactive')
}

function loadTrackers(fitBounds) {
    return performGetRequestWithFeedback(getApiRoute('trackers'), false)
    .then((response) => response.json())
    .then((json) => {
        if (!json['trackers']) return
        t = json['trackers']
        lngLats = new maptilersdk.LngLatBounds()
        for (let tracker of t) {
            if (!trackers[tracker.id]) {
                trackers[tracker.id] = tracker
            } else {
                trackers[tracker.id]['lat'] = tracker['lat']
                trackers[tracker.id]['lng'] = tracker['lng']
                trackers[tracker.id]['name'] = tracker['name']
                trackers[tracker.id]['ts'] = tracker['id']
                tracker = trackers[tracker.id]
                let track_source = map.getSource("route_" + tracker.id)
                if (track_source) {
                    updateTrack(tracker.id)
                }
            }

            if (tracker['lat'] && tracker['lng']) {
                if (tracker['marker']){
                    tracker["marker"].setLngLat([tracker['lng'], tracker['lat']])
                } else {
                    let popup = new maptilersdk.Popup({
                        className: 'map-popup',
                        closeButton: false
                    })
                        .setHTML("<span class='map-popup-name'>" + tracker['name'] + "</span><a class='map-popup-track-toggle inactive' id='map-popup-track-toggle-" + tracker.id + "' onclick='toggleTrack(" + tracker.id + ")'><span class='oi' data-glyph='location' aria-hidden='true'></span></a>")
                        .setMaxWidth("300px")
                        .addTo(map);
                    trackers[tracker.id]['marker'] = new maptilersdk.Marker()
                        .setLngLat([tracker['lng'], tracker['lat']])
                        .setPopup(popup)
                        .addTo(map);
                }
                lngLats.extend(new maptilersdk.LngLat(tracker['lng'], tracker['lat']))
            }
        }
        if (fitBounds) {
            map.fitBounds(lngLats, {
                maxZoom: 16
            })
        }
    })
}

function updateData() {
    loadTrackers(false)
    window.setTimeout(updateData, 10000)
}

function logout() {
    performPostWithFeedback(getApiRoute("logout"), {})
    .then((response) => response.json())
    .then((json) => {
        if (json["success"]) {
            window.location.reload()
        } else {
            console.error("Failed to log out... How?!")
        }
    })
}

function changePw() {
    document.getElementById("dialog-change-password").style.visibility = "visible"
    document.getElementById("menu").classList.remove("visible")
}

function checkLogin() {
    performGetRequestWithFeedback(getApiRoute('user'), true, false)
    .then((response) => response.json())
    .then((json) => {
        if (!json['name']) return
        document.getElementById('user-name').innerText = json['name']
        document.getElementById('user-section').style.visibility = 'visible'
        document.getElementById('content-code').style.visibility = 'hidden'
        document.getElementById('content-login-container').style.visibility = 'hidden'
        document.getElementById('map').style.visibility = 'visible'
        loadMap()
        loadTrackers(true)
        window.setTimeout(updateData, 10000)
    })
}

for (let element of document.getElementsByClassName("login-input")) {
    element.addEventListener("keyup", (e) => {
        if (e.keyCode == 13) {
            let username = document.getElementById('login-username').value
            let password = document.getElementById('login-password').value
            performPostWithFeedback(getApiRoute("login"), {username: username, password: password})
            .then((response) => response.json())
            .then((json) => {
                if(json['success']) {
                    checkLogin()
                }
            })
        }
    })
}

for (let element of document.getElementsByClassName("pw-change-input")) {
    element.addEventListener("keyup", (e) => {
        if (e.keyCode == 13) {
            let oldPassword = document.getElementById('change-old-password').value
            let newPassword1 = document.getElementById('change-password-1').value
            let newPassword2 = document.getElementById('change-password-2').value
            
            if (newPassword1 !== newPassword2) {
                alert("Passwords don't match")
            } else {
                performPostWithFeedback(getApiRoute('change_pw'), {
                    'oldpw': oldPassword,
                    'newpw': newPassword1
                })
                .then((response) => response.json())
                .then((json) => {
                    if (json['success']) {
                        alert("Password changed!")
                    } else {
                        alert("Wrong password!")
                    }
                })
            }

            document.getElementById('dialog-change-password').style.visibility = 'hidden'
        }
    })
}

document.getElementById("user-section").addEventListener("click", () => {
    document.getElementById("menu").classList.toggle("visible")
})

checkLogin()