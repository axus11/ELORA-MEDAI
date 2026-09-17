/* =========================================================
   ELORA MEDAI
   FUTURISTIC LOGIN ENGINE
========================================================= */


/* =========================================================
   SYSTEM CLOCK
========================================================= */

const systemTime = document.getElementById("systemTime");


function updateClock() {

    const now = new Date();

    const hours =
        String(now.getHours()).padStart(2, "0");

    const minutes =
        String(now.getMinutes()).padStart(2, "0");

    const seconds =
        String(now.getSeconds()).padStart(2, "0");

    systemTime.textContent =
        `${hours}:${minutes}:${seconds}`;
}


updateClock();

setInterval(updateClock, 1000);


/* =========================================================
   PASSWORD TOGGLE
========================================================= */

const password =
    document.getElementById("password");

const passwordToggle =
    document.getElementById("passwordToggle");


passwordToggle.addEventListener("click", () => {

    if (password.type === "password") {

        password.type = "text";

        passwordToggle.textContent = "◉";

    } else {

        password.type = "password";

        passwordToggle.textContent = "◉";
    }

});


/* =========================================================
   MOUSE LIGHT
========================================================= */

const cursorGlow =
    document.querySelector(".cursor-glow");


document.addEventListener("mousemove", (event) => {

    cursorGlow.style.left =
        `${event.clientX}px`;

    cursorGlow.style.top =
        `${event.clientY}px`;

});


/* =========================================================
   NEURAL NETWORK
========================================================= */

const canvas =
    document.getElementById("neuralCanvas");

const ctx =
    canvas.getContext("2d");


let particles = [];

let mouse = {
    x: null,
    y: null,
    radius: 180
};


function resizeCanvas() {

    canvas.width =
        window.innerWidth;

    canvas.height =
        window.innerHeight;

}


resizeCanvas();

window.addEventListener(
    "resize",
    resizeCanvas
);


document.addEventListener(
    "mousemove",
    (event) => {

        mouse.x = event.clientX;
        mouse.y = event.clientY;

    }
);


class Particle {

    constructor() {

        this.x =
            Math.random() *
            canvas.width;

        this.y =
            Math.random() *
            canvas.height;

        this.size =
            Math.random() * 1.8 + .4;

        this.speedX =
            (Math.random() - .5) * .35;

        this.speedY =
            (Math.random() - .5) * .35;

        this.opacity =
            Math.random() * .5 + .15;
    }


    update() {

        this.x += this.speedX;
        this.y += this.speedY;


        if (
            this.x < 0 ||
            this.x > canvas.width
        ) {
            this.speedX *= -1;
        }


        if (
            this.y < 0 ||
            this.y > canvas.height
        ) {
            this.speedY *= -1;
        }


        if (mouse.x !== null) {

            const dx =
                mouse.x - this.x;

            const dy =
                mouse.y - this.y;

            const distance =
                Math.sqrt(
                    dx * dx +
                    dy * dy
                );


            if (
                distance <
                mouse.radius
            ) {

                const force =
                    (mouse.radius - distance)
                    / mouse.radius;

                this.x -=
                    (dx / distance)
                    * force
                    * .25;

                this.y -=
                    (dy / distance)
                    * force
                    * .25;
            }

        }

    }


    draw() {

        ctx.beginPath();

        ctx.arc(
            this.x,
            this.y,
            this.size,
            0,
            Math.PI * 2
        );

        ctx.fillStyle =
            `rgba(0,220,255,${this.opacity})`;

        ctx.fill();

    }

}


function createParticles() {

    particles = [];

    const amount =
        Math.min(
            110,
            Math.floor(
                window.innerWidth / 12
            )
        );


    for (
        let i = 0;
        i < amount;
        i++
    ) {

        particles.push(
            new Particle()
        );

    }

}


createParticles();


function connectParticles() {

    for (
        let a = 0;
        a < particles.length;
        a++
    ) {

        for (
            let b = a + 1;
            b < particles.length;
            b++
        ) {

            const dx =
                particles[a].x -
                particles[b].x;

            const dy =
                particles[a].y -
                particles[b].y;

            const distance =
                Math.sqrt(
                    dx * dx +
                    dy * dy
                );


            if (distance < 120) {

                const opacity =
                    (1 - distance / 120)
                    * .12;


                ctx.beginPath();

                ctx.strokeStyle =
                    `rgba(0,210,255,${opacity})`;

                ctx.lineWidth = .6;

                ctx.moveTo(
                    particles[a].x,
                    particles[a].y
                );

                ctx.lineTo(
                    particles[b].x,
                    particles[b].y
                );

                ctx.stroke();

            }

        }

    }

}


function animateNetwork() {

    ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );


    particles.forEach(
        particle => {

            particle.update();

            particle.draw();

        }
    );


    connectParticles();


    requestAnimationFrame(
        animateNetwork
    );

}


animateNetwork();


/* =========================================================
   NEURAL LOAD SIMULATION
========================================================= */

const neuralLoad =
    document.getElementById("neuralLoad");


setInterval(() => {

    const value =
        Math.floor(
            Math.random() * 15
        ) + 80;

    neuralLoad.textContent =
        `${value}%`;

}, 1800);


/* =========================================================
   HEART RATE SIMULATION
========================================================= */

const heartRate =
    document.getElementById("heartRate");


setInterval(() => {

    const value =
        Math.floor(
            Math.random() * 7
        ) + 69;

    heartRate.textContent =
        value;

}, 2500);


/* =========================================================
   LOGIN ANIMATION
========================================================= */

const loginForm =
    document.getElementById("loginForm");

const loginButton =
    document.getElementById("loginButton");


loginForm.addEventListener(
    "submit",
    () => {

        loginButton.disabled = true;

        loginButton.querySelector(
            ".button-text"
        ).textContent =
            "AUTHENTICATING...";

        loginButton.querySelector(
            ".button-arrow"
        ).textContent =
            "◌";

    }
);