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
let openMessages = {}

fetch("static/script.js")
    .then((response) => response.text())
    .then((text) => animator.typeText = text)

async function performGetRequestWithFeedback(url, feedback=true, reloadOnDenied=true) {
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
        if (reloadOnDenied && response.status >= 400 && response.status < 500) {
            jwt = null
            logout()
        }
    })
    return promise
}

async function performPostWithFeedback(url, data) {
    animator.setPercentage(0)
    let csrfCookie = getCookie("csrf_access_token")
    headers = {
        "Content-Type": "application/json",
    }
    if (csrfCookie) {
        headers["X-CSRF-Token"] = csrfCookie
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

async function updateTrack(trackerId) {
    return performGetRequestWithFeedback(getApiRoute('track', [trackerId]), false)
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

function getCookie(cookieName) {
    let cookies = document.cookie.split(';')
    for(var cookie of cookies) {
        let split = cookie.split('=')
        let name = split[0].trim()
        if (name === cookieName) {
            return split[1].trim()
        }
    }
    return null
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

async function loadTrackers(fitBounds) {
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
                trackers[tracker.id]['ts'] = tracker['ts']
                trackers[tracker.id]['bat'] = tracker['bat']
                trackers[tracker.id]['rssi'] = tracker['rssi']
                trackers[tracker.id]['range'] = tracker['range']
                trackers[tracker.id]['sats'] = tracker['sats']
                tracker = trackers[tracker.id]
                let trackSource = map.getSource("route_" + tracker.id)
                if (trackSource) {
                    updateTrack(tracker.id)
                }
            }

            if (tracker['lat'] && tracker['lng']) {
                let source = map.getSource('route_' + tracker.id)
                let routeActive = !!source
                var toggleClasses = 'map-popup-track-toggle'
                if (!routeActive) {
                    toggleClasses += " inactive"
                }

                let date = new Date(tracker['ts'] * 1000)
                let displayTime = date.toLocaleTimeString()
                if (date.getDate() != new Date().getDate()) {
                    displayTime = date.toLocaleDateString() + " " + displayTime
                }
                let popupHtml = "<span class='map-popup-name'>" + 
                    encodeHtml(tracker['name']) + "</span><a class='" + 
                    toggleClasses + "' id='map-popup-track-toggle-" + 
                    tracker.id + "' onclick='toggleTrack(" + 
                    tracker.id + ")'><span class='eos-icons' aria-hidden='true' style='float: right; width: 1em; margin:0.2em 0 0.2em 0.2em'>route</span></a><br><span class='map-popup-ts'>" + 
                    displayTime + "</span><br><span class='eos-icons' aria-hidden='true'>battery_full</span>&nbsp;<span>" +
                    tracker['bat'] + "%</span><div style='float: right; display: inline; margin-left: 1em;'><span class='eos-icons' aria-hidden='true'>signal_cellular_alt</span>&nbsp;<span>" +
                    tracker['rssi'] + "%</span></div><br><span class='eos-icons' aria-hidden='true'>satellite_alt</span>&nbsp;<span>" +
                    tracker['sats'] + "</span><div style='float: right; display: inline; margin-left: 1em;'><span class='eos-icons' aria-hidden='true'>troubleshooting</span>&nbsp;<span>" +
                    tracker['range'] + "m</span></div>"
                if (tracker['marker']){
                    tracker["marker"].setLngLat([tracker['lng'], tracker['lat']])
                    map.getSource("tracker-circle-" + tracker.id).setData(createGeoJSONCircle([tracker['lng'], tracker['lat']], tracker['range']).data)
                    tracker["popup"].setHTML(popupHtml)
                } else {
                    let popup = new maptilersdk.Popup({
                        className: 'map-popup',
                        closeButton: false
                    })
                        .setHTML(popupHtml)
                        .setMaxWidth("300px")
                        .addTo(map);
                    trackers[tracker.id]['marker'] = new maptilersdk.Marker()
                        .setLngLat([tracker['lng'], tracker['lat']])
                        .setPopup(popup)
                        .addTo(map);
                    trackers[tracker.id]['popup'] = popup

                    map.addSource("tracker-circle-" + tracker.id, createGeoJSONCircle([tracker['lng'], tracker['lat']], tracker['range']))

                    map.addLayer({
                        'id': 'tracker-circle-layer-' + tracker.id,
                        "type": "fill",
                        "source": "tracker-circle-" + tracker.id,
                        "layout": {},
                        "paint": {
                            "fill-color": "#3FB5A0",
                            "fill-opacity": 0.4
                        }
                    })
                }
                lngLats.extend(new maptilersdk.LngLat(tracker['lng'], tracker['lat']))
            }

            if (tracker['bat'] < 15) {
                showMessage("battery_alert", "Battery of " + tracker["name"] + " is low.", 120000)
            }

            if (tracker['range'] > 20) {
                showMessage("gps_not_fixed", "Tracking of " + tracker["name"] + " is unreliable.", 30000)
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
        map.on('load', () => {
            loadTrackers(true)
            window.setTimeout(updateData, 10000)
        })
    })
}

function showMessage(icon, message, timeout=10000) {
    let msgCheck = icon + message
    let messageContainer = document.getElementById("message-container")
    if (msgCheck in openMessages) {
        window.clearTimeout(openMessages[msgCheck]['timer'])
    } else {
        openMessages[msgCheck] = {}
        let messageDiv = document.createElement("div")
        messageDiv.classList.add("message-element")
        let iconSpan = document.createElement("span")
        iconSpan.classList.add("eos-icons")
        iconSpan.classList.add("message-icon")
        iconSpan.innerText = icon
        messageDiv.appendChild(iconSpan)
        let messageSpan = document.createElement("span")
        messageSpan.textContent = message
        messageSpan.classList.add("message-text")
        messageDiv.appendChild(messageSpan)
        messageContainer.appendChild(messageDiv)
        openMessages[msgCheck]['div'] = messageDiv
    }

    openMessages[msgCheck]['timer'] = window.setTimeout(() => {
        messageContainer.removeChild(openMessages[msgCheck]['div'])
        delete openMessages[msgCheck]
    }, timeout)
}

function createGeoJSONCircle(center, radiusM) {
    let points = 128

    var coords = {
        latitude: center[1],
        longitude: center[0]
    }

    var km = radiusM / 1000

    var ret = []
    var distanceX = km/(111.320*Math.cos(coords.latitude*Math.PI/180))
    var distanceY = km/110.574

    var theta, x, y
    for(var i=0; i<points; i++) {
        theta = (i/points)*(2*Math.PI)
        x = distanceX*Math.cos(theta)
        y = distanceY*Math.sin(theta)

        ret.push([coords.longitude+x, coords.latitude+y])
    }
    ret.push(ret[0])

    return {
        "type": "geojson",
        "data": {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [ret]
                }
            }]
        }
    }
}

function encodeHtml(string) {
    let span = document.createElement('span');
    span.innerText = string;
    return span.innerHTML;
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

for (var element of document.getElementsByClassName("dialog-close")) {
    element.addEventListener("click", () => {
        console.log(element)
        element.parentElement.parentElement.style.visibility = 'hidden'
    })
}

checkLogin()