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

fetch("static/script.js")
    .then((response) => response.text())
    .then((text) => animator.typeText = text);

async function performRequestWithFeedback(url) {
    animator.setPercentage(0)
    let promise = fetch(url)
    promise.then(() => {animator.setPercentage(100)})
    return promise
}