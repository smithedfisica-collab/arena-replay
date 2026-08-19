// ======================================================
// CLIENTE - ARENA RAÍZES
// ======================================================

const waiting =
    document.getElementById("waiting");

const replayButton =
    document.getElementById("replayButton");


// ======================================================
// INFORMAÇÕES DA SESSÃO
// ======================================================

console.log(
    "SESSION_START:",
    SESSION_START
);

console.log(
    "SESSION_TOKEN:",
    SESSION_TOKEN
);


const sessionStart = new Date(

    SESSION_START.replace(
        " ",
        "T"
    )

);


// ======================================================
// ATUALIZAR TELA
//
// O botão só aparece quando o horário da
// sessão for atingido.
// ======================================================

function atualizarTela(){

    const agora = new Date();


    if(agora >= sessionStart){

        if(waiting){

            waiting.style.display = "none";

        }


        if(replayButton){

            replayButton.style.display = "block";

        }

    }

    else{

        if(waiting){

            waiting.style.display = "block";

        }


        if(replayButton){

            replayButton.style.display = "none";

        }

    }

}


atualizarTela();


setInterval(

    atualizarTela,

    1000

);


// ======================================================
// SOLICITAR REPLAY
// ======================================================

if(replayButton){

    replayButton.addEventListener(

        "click",

        async () => {


            // ==========================================
            // EVITAR CLIQUES DUPLOS DO MESMO CLIENTE
            //
            // Isso NÃO interfere em outros clientes
            // nem em outras atividades.
            // ==========================================

            if(replayButton.disabled){

                return;

            }


            replayButton.disabled = true;


            replayButton.innerHTML =
                "⏳ PROCESSANDO REPLAY...";


            try{


                const resposta = await fetch(

                    "/api/replay/request",

                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body: JSON.stringify({

                            token:
                                SESSION_TOKEN

                        })

                    }

                );


                const resultado =

                    await resposta.json();


                console.log(
                    "Resposta do replay:",
                    resultado
                );


                // ======================================
                // ERRO
                // ======================================

                if(

                    !resposta.ok

                    ||

                    !resultado.success

                ){

                    throw new Error(

                        resultado.message

                        ||

                        "Não foi possível solicitar o replay."

                    );

                }


                // ======================================
                // REPLAY ACEITO
                // ======================================

                replayButton.innerHTML =
                    "🎬 GERANDO REPLAY...";


                // Aguarda antes da primeira consulta.
                setTimeout(

                    verificarReplay,

                    1000

                );


            }

            catch(erro){


                console.error(
                    "Erro ao solicitar replay:",
                    erro
                );


                replayButton.innerHTML =
                    "❌ TENTAR NOVAMENTE";


                replayButton.disabled =
                    false;


                alert(

                    erro.message

                    ||

                    "Ocorreu um erro ao solicitar o replay."

                );

            }

        }

    );

}


// ======================================================
// VERIFICAR STATUS DO REPLAY
// ======================================================

async function verificarReplay(){


    try{


        const resposta = await fetch(

            `/api/replay/status/${SESSION_TOKEN}`,

            {

                cache: "no-store"

            }

        );


        const resultado =

            await resposta.json();


        console.log(
            "Status do replay:",
            resultado
        );


        // ==============================================
        // REPLAY PRONTO
        // ==============================================

        if(

            resultado.success

            &&

            resultado.status === "ready"

        ){


            replayButton.innerHTML =
                "✅ REPLAY PRONTO";


            replayButton.disabled =
                false;


            return;

        }


        // ==============================================
        // CONTINUA PROCESSANDO
        // ==============================================

        setTimeout(

            verificarReplay,

            1500

        );


    }

    catch(erro){


        console.error(
            "Erro ao verificar replay:",
            erro
        );


        // Tenta novamente depois de 2 segundos.

        setTimeout(

            verificarReplay,

            2000

        );

    }

}