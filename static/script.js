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
        this.boxShadowS = Math.round(Math.abs((((this.lightingCycle + 10) / 40) % 10) - 5) + 5) + "px"

        var r = 0x3F
        var g = 0xB5
        var b = 0xA0

        r = Math.round(r * (Math.abs(((this.lightingCycle) % 400) - 200) / 280)) + 40
        g = Math.round(g * (Math.abs(((this.lightingCycle) % 400) - 200) / 280)) + 40
        b = Math.round(b * (Math.abs(((this.lightingCycle) % 400) - 200) / 280)) + 40

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
        this.lightingCycle++
        if (this.lightingCycle % 10 !== 0) return

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

var jwt = null
var map = null
let trackers = {}

fetch("static/script.js")
    .then((response) => response.text())
    .then((text) => animator.typeText = text)

async function performRequestWithFeedback(url) {
    animator.setPercentage(0)
    headers = {}

    if (jwt != null) {
        headers['Authorization'] = "JWT " + jwt
    }

    let promise = fetch(url, {
        headers: headers
    })
    promise.then(() => {animator.setPercentage(100)})
    return promise
}

async function performPostWithFeedback(url, data) {
    animator.setPercentage(0)
    headers = {
        "Content-Type": "application/json",
    }

    if (jwt != null) {
        headers['Authorization'] = "JWT " + jwt
    }

    let promise = fetch(url, {
        method: "POST",
        mode: "cors",
        cache: "no-cache",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data)
    })
    promise.then(() => {animator.setPercentage(100)})
    return promise
}

function toggleTrack(trackerId) {
    let toggleA = document.getElementById('map-popup-track-toggle-' + trackerId)
    if (toggleA.classList.contains('inactive')) {
        performRequestWithFeedback('/api/v1/track/' + trackerId)
        .then((response) => response.json())
        .then((json) => {
            track = Array.from(json, (_) => [_["lng"], _["lat"]])
            map.addSource('route_' + trackerId, {
                'type': 'geojson',
                'data': {
                    'type': 'Feature',
                    'properties': {},
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': track
                    }
                }
            })
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

function loadTrackers() {
    performRequestWithFeedback('/api/v1/trackers')
    .then((response) => response.json())
    .then((json) => {
        if (!json['trackers']) return
        t = json['trackers']
        lngLats = new maptilersdk.LngLatBounds()
        for (tracker of t) {
            trackers[tracker.id] = tracker

            if (tracker['lat'] && tracker['lng']) {
                let popup = new maptilersdk.Popup({className: 'map-popup'})
                    .setHTML("<span class='map-popup-name'>" + tracker['name'] + "</span><a class='map-popup-track-toggle inactive' id='map-popup-track-toggle-" + tracker.id + "' onclick='toggleTrack(" + tracker.id + ")'><span class='oi' data-glyph='location' aria-hidden='true'></span></a>")
                    .setMaxWidth("300px")
                    .addTo(map);
                trackers[tracker.id]['marker'] = new maptilersdk.Marker()
                    .setLngLat([tracker['lng'], tracker['lat']])
                    .setPopup(popup)
                    .addTo(map);
                lngLats.extend(new maptilersdk.LngLat(tracker['lng'], tracker['lat']))
            }
        }
        console.log(lngLats)
        map.fitBounds(lngLats, {
            maxZoom: 16
        })
    })
}



for (element of document.getElementsByClassName("login-input")) {
    console.log(element)
    element.addEventListener("keyup", (e) => {
        if (e.keyCode == 13) {
            let username = document.getElementById('login-username').value
            let password = document.getElementById('login-password').value
            performPostWithFeedback("/api/v1/login", {username: username, password: password})
            .then((response) => response.json())
            .then((json) => { jwt = json['access_token']})
            .then(() => performRequestWithFeedback('/api/v1/user'))
            .then((response) => response.json())
            .then((json) => {
                if (!json['name']) return
                document.getElementById('user-name').innerText = json['name']
                document.getElementById('user-section').style.visibility = 'visible'
                document.getElementById('content-code').style.visibility = 'hidden'
                document.getElementById('content-login-container').style.visibility = 'hidden'
                document.getElementById('map').style.visibility = 'visible'
                loadMap()
                loadTrackers()
            })
        }
    })
}