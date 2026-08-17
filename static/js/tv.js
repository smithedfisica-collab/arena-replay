let ultimoModo = "";
let countdownExecutando = false;

const liveBadge =
    document.getElementById("liveBadge");

const replayOverlay =
    document.getElementById("replayOverlay");

const countdown =
    document.getElementById("countdown");


function esperar(ms) {

    return new Promise(
        resolve => setTimeout(resolve, ms)
    );

}


function mostrarLive() {

    replayOverlay.style.display = "none";

    countdownExecutando = false;

}


async function mostrarCountdown() {

    if (countdownExecutando) {
        return;
    }

    countdownExecutando = true;

    replayOverlay.style.display = "flex";


    countdown.innerHTML = "3";

    await esperar(1000);

    countdown.innerHTML = "2";

    await esperar(1000);

    countdown.innerHTML = "1";

    await esperar(1000);

    replayOverlay.style.display = "none";

    countdownExecutando = false;

}


function mostrarReplay() {

    replayOverlay.style.display = "none";

    countdownExecutando = false;

}


async function verificarEstado() {

    try {

        const resposta =
            await fetch("/tv/status", {
                cache: "no-store"
            });

        const estado =
            await resposta.json();


        if (liveBadge) {

            liveBadge.innerHTML =
                estado.mode.toUpperCase();

        }


        if (estado.mode === ultimoModo) {
            return;
        }


        ultimoModo = estado.mode;


        switch (estado.mode) {

            case "live":

                mostrarLive();

                break;


            case "countdown":

                mostrarCountdown();

                break;


            case "replay":

                mostrarReplay();

                break;

        }

    }
    catch (erro) {

        console.error(
            "Erro ao verificar TV:",
            erro
        );

    }

}


setInterval(
    verificarEstado,
    250
);


verificarEstado();