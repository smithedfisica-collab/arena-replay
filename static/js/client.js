// ======================================================
// CLIENTE ARENA REPLAY
// ======================================================

const waiting = document.getElementById("waiting");
const replayButton = document.getElementById("replayButton");

console.log("Data recebida:", SESSION_START);

const sessionStart = new Date(
    SESSION_START.replace(" ", "T")
);

console.log("Data convertida:", sessionStart);

function atualizarTela(){

    const agora = new Date();

    console.log("Agora:", agora);
    console.log("Sessão:", sessionStart);

    if(agora >= sessionStart){

        console.log("LIBERANDO BOTÃO");

        waiting.style.display = "none";
        replayButton.style.display = "block";

    }else{

        console.log("AINDA NÃO");

        waiting.style.display = "block";
        replayButton.style.display = "none";

    }

}

atualizarTela();

setInterval(atualizarTela,1000);

// ======================================================
// BOTÃO REPLAY
// ======================================================

replayButton.addEventListener("click", async () => {

    replayButton.disabled = true;

    replayButton.innerHTML = "⏳ PROCESSANDO...";

    const resposta = await fetch("/api/replay/request",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({

            token:SESSION_TOKEN

        })

    });

    const resultado = await resposta.json();

    console.log(resultado);

    replayButton.innerHTML="✅ REPLAY ENVIADO";

});