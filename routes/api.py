from flask import Blueprint, Response, jsonify, request

from camera.camera import Camera
from replay.buffer import ReplayBuffer
from replay.save_replay import save_replay

from database import tv_state
from database.database import get_connection

import os
import cv2
import time
import threading


# ======================================================
# BLUEPRINT
# ======================================================

api_bp = Blueprint(
    "api",
    __name__
)


# ======================================================
# CONFIGURAÇÕES
# ======================================================

# FPS usado para:
# - transmissão da TV
# - buffer do replay
# - arquivo MP4 salvo
#
# 15 FPS deixa o sistema bem mais leve e o movimento
# continua natural para o replay.
FPS = 15


# Quantidade de segundos que queremos guardar
BUFFER_SECONDS = 20


# Total máximo de frames do replay
MAX_FRAMES = FPS * BUFFER_SECONDS


# ======================================================
# SISTEMAS DE CÂMERA
# ======================================================

# ------------------------------------------------------
# QUADRA 1
# ------------------------------------------------------

# ------------------------------------------------------
# SISTEMA DE CÂMERAS
# ------------------------------------------------------
#
# Um único objeto Camera controla:
#
# - Quadra 1 ao vivo
# - Quadra 1 replay
# - Ping Pong 1 replay
# ------------------------------------------------------

quadra_camera = Camera()


# ------------------------------------------------------
# BUFFER DA QUADRA 1
# ------------------------------------------------------

quadra_buffer = ReplayBuffer(
    MAX_FRAMES
)


# ------------------------------------------------------
# BUFFER DO PING PONG 1
# ------------------------------------------------------

pingpong_buffer = ReplayBuffer(
    MAX_FRAMES
)


# ======================================================
# TODOS OS SISTEMAS
# ======================================================

CAMERA_SYSTEMS = {

    "Quadra 1": {

        "camera": quadra_camera,

        "buffer": quadra_buffer

    },

    "Ping Pong 1": {

        # Usa o mesmo objeto Camera.
        #
        # Dentro dele existe a conexão específica
        # da câmera do Ping Pong.
        "camera": quadra_camera,

        "buffer": pingpong_buffer

    }

}


# ======================================================
# ÚLTIMO FRAME DA CÂMERA
# ======================================================

latest_frame = None

frame_lock = threading.Lock()


# ======================================================
# CONTROLE DE INÍCIO DA THREAD
# ======================================================

camera_thread_started = False

camera_thread_lock = threading.Lock()


# ======================================================
# CAPTURA CONTÍNUA DA CÂMERA
# ======================================================

# ======================================================
# CAPTURA CONTÍNUA DAS CÂMERAS
# ======================================================

def capture_camera():

    global latest_frame


    print("=" * 60)
    print("CAPTURA CONTÍNUA DAS CÂMERAS INICIADA")
    print("=" * 60)

    print("TV AO VIVO: QUADRA 1")
    print("REPLAY QUADRA 1: STREAM 2")
    print("REPLAY PING PONG 1: STREAM 2")

    print("=" * 60)


    # ==================================================
    # OBJETO PRINCIPAL DAS CÂMERAS
    # ==================================================

    camera = quadra_camera


    # ==================================================
    # BUFFERS
    # ==================================================

    quadra_replay_buffer = quadra_buffer

    pingpong_replay_buffer = pingpong_buffer


    # ==================================================
    # CONTROLE PARA NÃO DUPLICAR FRAMES
    # ==================================================

    last_quadra_sequence = -1

    last_pingpong_sequence = -1


    while True:

        try:


            # ==============================================
            # AO VIVO DA QUADRA 1
            #
            # SOMENTE ESTE FRAME VAI PARA A TV.
            # ==============================================

            live_frame = camera.get_frame()


            if live_frame is not None:

                with frame_lock:

                    latest_frame = live_frame


            # ==============================================
            # REPLAY DA QUADRA 1
            # ==============================================

            (
                quadra_replay_frame,
                quadra_sequence

            ) = camera.get_replay_frame_with_sequence()


            if (

                quadra_replay_frame is not None

                and

                quadra_sequence != last_quadra_sequence

            ):

                quadra_replay_buffer.add_frame(

                    quadra_replay_frame

                )


                last_quadra_sequence = (

                    quadra_sequence

                )


            # ==============================================
            # REPLAY DO PING PONG 1
            #
            # NÃO VAI PARA A TV AO VIVO.
            #
            # APENAS ALIMENTA O BUFFER DE REPLAY.
            # ==============================================

            (
                pingpong_replay_frame,
                pingpong_sequence

            ) = camera.get_pingpong_frame_with_sequence()


            if (

                pingpong_replay_frame is not None

                and

                pingpong_sequence != last_pingpong_sequence

            ):

                pingpong_replay_buffer.add_frame(

                    pingpong_replay_frame

                )


                last_pingpong_sequence = (

                    pingpong_sequence

                )


            # ==============================================
            # PEQUENA PAUSA
            #
            # Evita usar 100% da CPU.
            # ==============================================

            time.sleep(

                0.002

            )


        except Exception as e:


            print("=" * 60)
            print("ERRO NA CAPTURA DAS CÂMERAS")
            print(e)
            print("=" * 60)


            time.sleep(

                0.5

            )


# ======================================================
# INICIAR CÂMERA UMA ÚNICA VEZ
# ======================================================

def start_camera_thread():

    global camera_thread_started


    with camera_thread_lock:

        if camera_thread_started:

            return


        camera_thread = threading.Thread(

            target=capture_camera,

            daemon=True

        )


        camera_thread.start()


        camera_thread_started = True


        print("=" * 60)
        print("THREAD DA CÂMERA INICIADA")
        print("=" * 60)


# Inicia imediatamente
start_camera_thread()


# ======================================================
# OBTER ÚLTIMO FRAME
# ======================================================

def get_latest_frame():

    global latest_frame


    with frame_lock:

        if latest_frame is None:

            return None


        return latest_frame.copy()


# ======================================================
# CODIFICAR FRAME PARA JPEG
# ======================================================

def encode_frame(frame):

    if frame is None:

        return None


    success, encoded_frame = cv2.imencode(

        ".jpg",

        frame,

        [

            cv2.IMWRITE_JPEG_QUALITY,

            80

        ]

    )


    if not success:

        return None


    return encoded_frame.tobytes()


# ======================================================
# ENVIAR FRAME PARA STREAM
# ======================================================

def stream_frame(frame):

    encoded = encode_frame(
        frame
    )


    if encoded is None:

        return None


    return (

        b"--frame\r\n"

        b"Content-Type: image/jpeg\r\n\r\n"

        +

        encoded

        +

        b"\r\n"

    )


# ======================================================
# TRANSMISSÃO DE FRAMES DA TV
# ======================================================

def generate_frames():

    # Controle preciso do tempo do stream
    next_frame_time = time.perf_counter()


    while True:

        try:

            # ==================================================
            # MODO COUNTDOWN
            # ==================================================

            if tv_state.tv_mode == "countdown":

                elapsed = (

                    time.time()

                    -

                    tv_state.countdown_start

                )


                # ----------------------------------------------
                # TERMINOU O 3, 2, 1
                # ----------------------------------------------

                if elapsed >= tv_state.countdown_seconds:

                    tv_state.tv_mode = "replay"

                    tv_state.replay_index = 0

                    next_frame_time = (
                        time.perf_counter()
                    )

                    continue


                # ----------------------------------------------
                # Durante a contagem continua mostrando
                # a câmera AO VIVO.
                #
                # O HTML mostra o 3, 2, 1 por cima.
                # ----------------------------------------------

                frame = get_latest_frame()


                if frame is None:

                    time.sleep(
                        0.01
                    )

                    continue


                data = stream_frame(
                    frame
                )


                if data is not None:

                    yield data


            # ==================================================
            # MODO REPLAY
            # ==================================================

            elif tv_state.tv_mode == "replay":

                # ----------------------------------------------
                # TERMINOU O REPLAY
                # ----------------------------------------------

                if (

                    not tv_state.replay_frames

                    or

                    tv_state.replay_index
                    >=
                    len(tv_state.replay_frames)

                ):

                    print("=" * 60)
                    print("REPLAY FINALIZADO")
                    print("=" * 60)


                    tv_state.tv_mode = "live"

                    tv_state.replay_index = 0

                    tv_state.replay_frames = []


                    next_frame_time = (
                        time.perf_counter()
                    )

                    continue


                # ----------------------------------------------
                # PEGA O PRÓXIMO FRAME
                # ----------------------------------------------

                frame = tv_state.replay_frames[

                    tv_state.replay_index

                ]


                tv_state.replay_index += 1


                data = stream_frame(
                    frame
                )


                if data is not None:

                    yield data


            # ==================================================
            # MODO AO VIVO
            # ==================================================

            else:

                if tv_state.tv_mode != "live":

                    tv_state.tv_mode = "live"


                frame = get_latest_frame()


                if frame is None:

                    time.sleep(
                        0.01
                    )

                    continue


                data = stream_frame(
                    frame
                )


                if data is not None:

                    yield data


            # ==================================================
            # CONTROLE DE FPS
            #
            # A transmissão fica limitada a 15 FPS.
            #
            # Isso evita:
            #
            # - CPU em 100%
            # - centenas de JPEGs por segundo
            # - travamentos
            # - atraso acumulado
            # ==================================================

            next_frame_time += (

                1 / FPS

            )


            remaining_time = (

                next_frame_time

                -

                time.perf_counter()

            )


            if remaining_time > 0:

                time.sleep(
                    remaining_time
                )


            else:

                # Se atrasou, reinicia o relógio
                # para não acumular atraso.

                next_frame_time = (

                    time.perf_counter()

                )


        except GeneratorExit:

            return


        except Exception as e:

            print("=" * 60)
            print("ERRO NA TRANSMISSÃO DA TV")
            print(e)
            print("=" * 60)

            time.sleep(
                0.1
            )


# ======================================================
# ROTA DO STREAM DA TV
#
# ESSA ROTA É FUNDAMENTAL.
#
# O ERRO:
#
# BuildError:
# Could not build url for endpoint 'api.video_feed'
#
# acontecia porque ela tinha desaparecido.
# ======================================================

@api_bp.route(
    "/video_feed"
)
def video_feed():

    return Response(

        generate_frames(),

        mimetype=(

            "multipart/x-mixed-replace; "

            "boundary=frame"

        ),

        headers={

            "Cache-Control":

                "no-cache, no-store, must-revalidate",

            "Pragma":

                "no-cache",

            "Expires":

                "0"

        }

    )


# ======================================================
# SALVAR REPLAY PARA UM ALUGUEL
# ======================================================

def save_replay_for_rental(

    rental_id,

    frames=None

):

    print("=" * 60)
    print("SALVANDO REPLAY PARA O ALUGUEL")
    print("RENTAL ID:", rental_id)
    print("=" * 60)


    # ==================================================
    # BUSCAR ESPAÇO
    # ==================================================

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(

        """

        SELECT court

        FROM rentals

        WHERE id = ?

        """,

        (

            rental_id,

        )

    )


    rental = cursor.fetchone()

    conn.close()


    if rental is None:

        return {

            "success": False,

            "message": "Aluguel não encontrado."

        }


    court = rental[
        "court"
    ]


    # ==================================================
    # SE NÃO RECEBEU FRAMES,
    # PEGA DO BUFFER
    # ==================================================

    if frames is None:

        camera_system = CAMERA_SYSTEMS.get(
            court
        )


        if camera_system is None:

            return {

                "success": False,

                "message":

                    f"Nenhuma câmera configurada para {court}."

            }


        buffer = camera_system[
            "buffer"
        ]


        frames = buffer.get_frames()


    # ==================================================
    # VERIFICAR FRAMES
    # ==================================================

    if not frames:

        return {

            "success": False,

            "message":

                "Nenhum frame disponível."

        }


    # ==================================================
    # SALVAR VÍDEO
    # ==================================================

    filepath = save_replay(

        frames,

        FPS

    )


    if not filepath:

        return {

            "success": False,

            "message":

                "Não foi possível salvar o vídeo."

        }


    filename = os.path.basename(
        filepath
    )


    print("=" * 60)
    print("ARQUIVO CRIADO")
    print("FILENAME:", filename)
    print("=" * 60)


    # ==================================================
    # REGISTRAR NO BANCO
    # ==================================================

    conn = get_connection()

    cursor = conn.cursor()


    try:

        cursor.execute(

            """

            INSERT INTO replays

            (

                rental_id,

                filename

            )

            VALUES (?, ?)

            """,

            (

                rental_id,

                filename

            )

        )


        conn.commit()


        print("=" * 60)
        print("REPLAY REGISTRADO NO BANCO")
        print("RENTAL ID:", rental_id)
        print("FILENAME:", filename)
        print("=" * 60)


        return {

            "success": True,

            "filename": filename

        }


    except Exception as e:

        conn.rollback()


        print("=" * 60)
        print("ERRO AO REGISTRAR REPLAY")
        print(e)
        print("=" * 60)


        return {

            "success": False,

            "message": str(e)

        }


    finally:

        conn.close()


# ======================================================
# SALVAR REPLAY EM SEGUNDO PLANO
# ======================================================

def save_replay_background(

    rental_id,

    frames

):

    try:

        print("=" * 60)
        print("SALVAMENTO EM SEGUNDO PLANO")
        print("RENTAL ID:", rental_id)
        print("FRAMES:", len(frames))
        print("=" * 60)


        result = save_replay_for_rental(

            rental_id,

            frames

        )


        if result.get("success"):

            tv_state.last_replay = (

                result.get(
                    "filename"
                )

            )


            print("REPLAY SALVO COM SUCESSO")


        else:

            print(
                "ERRO AO SALVAR REPLAY:",
                result.get("message")
            )


    except Exception as e:

        print("=" * 60)
        print("ERRO NO SALVAMENTO EM SEGUNDO PLANO")
        print(e)
        print("=" * 60)


# ======================================================
# SALVAR REPLAY MANUALMENTE
# ======================================================

@api_bp.route(
    "/save_replay"
)
def save_current_replay():

    camera_system = CAMERA_SYSTEMS.get(
        "Quadra 1"
    )


    if camera_system is None:

        return "Sistema da Quadra 1 não encontrado."


    buffer = camera_system[
        "buffer"
    ]


    frames = buffer.get_frames()


    if not frames:

        return "Nenhum replay disponível."


    filepath = save_replay(

        frames,

        FPS

    )


    if filepath:

        return (

            "Replay salvo em:<br><br>"

            +

            filepath

        )


    return "Não foi possível salvar o replay."


# ======================================================
# STATUS DA TV
# ======================================================

@api_bp.route(
    "/tv/status"
)
def tv_status():

    camera_system = CAMERA_SYSTEMS.get(
        "Quadra 1"
    )


    buffer_frames = 0


    if camera_system is not None:

        buffer = camera_system[
            "buffer"
        ]


        frames = buffer.get_frames()


        buffer_frames = len(
            frames
        )


    return jsonify({

        "mode":

            tv_state.tv_mode,


        "last_replay":

            tv_state.last_replay,


        "buffer_frames":

            buffer_frames,


        "buffer_seconds":

            round(

                buffer_frames / FPS,

                1

            )


    })


# ======================================================
# CLIENTE SOLICITA REPLAY
# ======================================================

@api_bp.route(

    "/api/replay/request",

    methods=["POST"]

)
def request_replay():

    # ==================================================
    # RECEBER TOKEN
    # ==================================================

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({

            "success": False,

            "message": "Dados inválidos."

        }), 400


    token = data.get(
        "token"
    )


    if not token:

        return jsonify({

            "success": False,

            "message": "Token não informado."

        }), 400


    # ==================================================
    # NÃO DEIXAR DOIS REPLAYS AO MESMO TEMPO
    # ==================================================

    if tv_state.tv_mode != "live":

        return jsonify({

            "success": False,

            "message":

                "Já existe um replay em andamento."

        }), 409


    print("=" * 60)
    print("REPLAY SOLICITADO")
    print("TOKEN:", token)
    print("=" * 60)


    # ==================================================
    # BUSCAR ALUGUEL
    # ==================================================

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(

        """

        SELECT

            id,

            court

        FROM rentals

        WHERE public_token = ?

        """,

        (

            token,

        )

    )


    rental = cursor.fetchone()

    conn.close()


    if rental is None:

        return jsonify({

            "success": False,

            "message":

                "Reserva não encontrada."

        }), 404


    rental_id = rental[
        "id"
    ]


    court = rental[
        "court"
    ]


    # ==================================================
    # BUSCAR SISTEMA DA CÂMERA
    # ==================================================

    camera_system = CAMERA_SYSTEMS.get(
        court
    )


    if camera_system is None:

        return jsonify({

            "success": False,

            "message":

                f"Nenhuma câmera configurada para {court}."

        }), 500


    camera = camera_system.get(
        "camera"
    )


    if camera is None:

        return jsonify({

            "success": False,

            "message":

                f"A câmera de {court} ainda não está configurada."

        }), 500


    # ==================================================
    # CONGELAR BUFFER AGORA
    #
    # Esse replay será enviado imediatamente para a TV.
    # ==================================================

    buffer = camera_system[
        "buffer"
    ]


    frames = buffer.get_frames()


    if not frames:

        return jsonify({

            "success": False,

            "message":

                "Nenhum frame disponível para o replay."

        }), 500


    # ==================================================
    # PREPARAR TV IMEDIATAMENTE
    #
    # Não esperamos salvar o MP4.
    # ==================================================

    tv_state.replay_frames = frames

    tv_state.replay_index = 0

    tv_state.countdown_seconds = 3

    tv_state.countdown_start = time.time()

    tv_state.tv_mode = "countdown"


    print("=" * 60)
    print("REPLAY ENVIADO PARA A TV")
    print("CONTAGEM: 3, 2, 1")
    print("FRAMES:", len(frames))
    print("=" * 60)


    # ==================================================
    # SALVAR EM SEGUNDO PLANO
    # ==================================================

    save_thread = threading.Thread(

        target=save_replay_background,

        args=(

            rental_id,

            frames

        ),

        daemon=True

    )


    save_thread.start()


    # ==================================================
    # RESPONDER IMEDIATAMENTE
    # ==================================================

    return jsonify({

        "success": True,

        "message":

            "Replay enviado para a TV.",


        "status":

            "processing",


        "frames":

            len(frames)

    })


# ======================================================
# STATUS DO REPLAY DO CLIENTE
# ======================================================

@api_bp.route(
    "/api/replay/status/<public_token>"
)
def replay_status(public_token):

    conn = get_connection()

    cursor = conn.cursor()


    # ==================================================
    # BUSCAR RESERVA
    # ==================================================

    cursor.execute(

        """

        SELECT

            id,

            customer_name,

            court,

            scheduled_date,

            scheduled_time,

            duration,

            status,

            public_token

        FROM rentals

        WHERE public_token = ?

        """,

        (

            public_token,

        )

    )


    rental = cursor.fetchone()


    if rental is None:

        conn.close()


        return jsonify({

            "success": False,

            "message":

                "Reserva não encontrada."

        }), 404


    # ==================================================
    # BUSCAR REPLAYS
    # ==================================================

    cursor.execute(

        """

        SELECT

            id,

            filename,

            created_at

        FROM replays

        WHERE rental_id = ?

        ORDER BY id ASC

        """,

        (

            rental["id"],

        )

    )


    replay_rows = cursor.fetchall()


    replays = []


    for replay in replay_rows:

        replays.append({

            "id":

                replay["id"],


            "filename":

                replay["filename"],


            "created_at":

                replay["created_at"]

        })


    conn.close()


    return jsonify({

        "success":

            True,


        "id":

            rental["id"],


        "customer_name":

            rental["customer_name"],


        "court":

            rental["court"],


        "scheduled_date":

            rental["scheduled_date"],


        "scheduled_time":

            rental["scheduled_time"],


        "duration":

            rental["duration"],


        "status":

            rental["status"],


        "public_token":

            rental["public_token"],


        "replays":

            replays

    })