from flask import Blueprint, jsonify, request

from camera.camera import Camera
from replay.buffer import ReplayBuffer
from replay.save_replay import save_replay
from database.database import get_connection

import os
import time
import threading

from datetime import datetime, timedelta


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

# FPS usado no buffer e no arquivo final.
# Mantendo os dois iguais, o replay fica na velocidade real.
FPS = 15


# Quantidade de segundos guardados no buffer.
BUFFER_SECONDS = 20


# Quantidade máxima de frames.
MAX_FRAMES = FPS * BUFFER_SECONDS


# ======================================================
# SISTEMA DE CÂMERA
# ======================================================
#
# NÃO EXISTE MAIS TRANSMISSÃO AO VIVO.
#
# A câmera é usada somente para alimentar os buffers
# de replay da Quadra 1 e do Ping Pong 1.
# ======================================================

quadra_camera = Camera()


# ======================================================
# BUFFER DA QUADRA 1
# ======================================================

quadra_buffer = ReplayBuffer(
    MAX_FRAMES
)


# ======================================================
# BUFFER DO PING PONG 1
# ======================================================

pingpong_buffer = ReplayBuffer(
    MAX_FRAMES
)


# ======================================================
# SISTEMAS DE REPLAY
# ======================================================

CAMERA_SYSTEMS = {

    "Quadra 1": {

        "camera": quadra_camera,

        "buffer": quadra_buffer

    },

    "Ping Pong 1": {

        "camera": quadra_camera,

        "buffer": pingpong_buffer

    }

}


# ======================================================
# CONTROLE DE INÍCIO DA THREAD DA CÂMERA
# ======================================================

camera_thread_started = False

camera_thread_lock = threading.Lock()


# ======================================================
# CONTROLE DOS REPLAYS EM PROCESSAMENTO
# ======================================================
#
# Cada replay possui seu próprio status.
#
# processing
# ready
# error
#
# Isso permite que Quadra 1 e Ping Pong 1 processem
# replays simultaneamente.
# ======================================================

replay_jobs = {}

replay_jobs_lock = threading.Lock()


def set_replay_job(

    job_id,

    status,

    message="",

    filename=None

):

    with replay_jobs_lock:

        replay_jobs[job_id] = {

            "status": status,

            "message": message,

            "filename": filename,

            "updated_at": time.time()

        }


        # Mantém somente os 200 jobs mais recentes.
        if len(replay_jobs) > 200:

            oldest = sorted(

                replay_jobs.items(),

                key=lambda item: item[1].get(
                    "updated_at",
                    0
                )

            )[:-200]


            for old_job_id, _ in oldest:

                replay_jobs.pop(
                    old_job_id,
                    None
                )


def get_replay_job(

    job_id

):

    with replay_jobs_lock:

        job = replay_jobs.get(
            job_id
        )


        if job is None:

            return None


        return dict(
            job
        )


# ======================================================
# CAPTURA CONTÍNUA DOS REPLAYS
# ======================================================
#
# NÃO EXISTE MAIS:
#
# camera.get_frame()
# TV AO VIVO
# latest_frame
# video_feed
#
# A câmera é acessada somente pelos dois streams
# de replay.
# ======================================================

def capture_camera():

    print("=" * 60)
    print("CAPTURA DE REPLAY INICIADA")
    print("REPLAY QUADRA 1")
    print("REPLAY PING PONG 1")
    print("SEM TRANSMISSÃO AO VIVO")
    print("=" * 60)


    camera = quadra_camera


    # Controle para não adicionar
    # o mesmo frame duas vezes.
    last_quadra_sequence = -1

    last_pingpong_sequence = -1


    # O buffer recebe exatamente FPS frames
    # por segundo, no máximo.
    intervalo_frame = 1 / FPS

    next_buffer_time = time.perf_counter()


    while True:

        try:

            agora = time.perf_counter()


            if agora >= next_buffer_time:


                # ==========================================
                # REPLAY DA QUADRA 1
                # ==========================================

                (
                    quadra_replay_frame,
                    quadra_sequence
                ) = camera.get_replay_frame_with_sequence()


                if (

                    quadra_replay_frame is not None

                    and

                    quadra_sequence != last_quadra_sequence

                ):

                    quadra_buffer.add_frame(
                        quadra_replay_frame
                    )


                    last_quadra_sequence = (
                        quadra_sequence
                    )


                # ==========================================
                # REPLAY DO PING PONG 1
                # ==========================================

                (
                    pingpong_replay_frame,
                    pingpong_sequence
                ) = camera.get_pingpong_frame_with_sequence()


                if (

                    pingpong_replay_frame is not None

                    and

                    pingpong_sequence != last_pingpong_sequence

                ):

                    pingpong_buffer.add_frame(
                        pingpong_replay_frame
                    )


                    last_pingpong_sequence = (
                        pingpong_sequence
                    )


                # Próxima atualização dos buffers.
                next_buffer_time = (
                    agora + intervalo_frame
                )


            time.sleep(
                0.002
            )


        except Exception as e:

            print("=" * 60)
            print("ERRO NA CAPTURA DOS REPLAYS")
            print(e)
            print("=" * 60)


            time.sleep(
                0.5
            )


# ======================================================
# INICIAR THREAD DA CÂMERA
# ======================================================

def start_camera_thread():

    global camera_thread_started


    with camera_thread_lock:

        if camera_thread_started:

            return


        camera_thread = threading.Thread(

            target=capture_camera,

            daemon=True,

            name="ReplayCapture"

        )


        camera_thread.start()


        camera_thread_started = True


        print("=" * 60)
        print("THREAD DE CAPTURA DE REPLAY INICIADA")
        print("=" * 60)


# ======================================================
# INICIAR CAPTURA
# ======================================================

start_camera_thread()


# ======================================================
# SALVAR REPLAY PARA O ALUGUEL
# ======================================================

def save_replay_for_rental(

    rental_id,

    frames,

    job_id=None

):

    conn = None


    try:


        # ==============================================
        # VERIFICAR FRAMES
        # ==============================================

        if frames is None or len(frames) == 0:

            message = (
                "Nenhum frame disponível."
            )


            if job_id:

                set_replay_job(

                    job_id,

                    "error",

                    message

                )


            return {

                "success": False,

                "message": message

            }


        # ==============================================
        # CONGELAR OS FRAMES
        # ==============================================

        frozen_frames = []


        for frame in frames:

            if frame is None:

                continue


            try:

                frozen_frames.append(
                    frame.copy()
                )


            except Exception:

                frozen_frames.append(
                    frame
                )


        if not frozen_frames:

            message = (
                "Nenhum frame válido disponível."
            )


            if job_id:

                set_replay_job(

                    job_id,

                    "error",

                    message

                )


            return {

                "success": False,

                "message": message

            }


        print("=" * 60)
        print("INICIANDO GRAVAÇÃO DO REPLAY")
        print("RENTAL ID:", rental_id)
        print("FRAMES:", len(frozen_frames))
        print("FPS:", FPS)
        print("=" * 60)


        # ==============================================
        # SALVAR ARQUIVO
        # ==============================================

        filepath = save_replay(

            frozen_frames,

            FPS

        )


        if not filepath:

            message = (
                "A função save_replay não retornou "
                "o caminho do arquivo."
            )


            if job_id:

                set_replay_job(

                    job_id,

                    "error",

                    message

                )


            return {

                "success": False,

                "message": message

            }


        # ==============================================
        # VERIFICAR SE O ARQUIVO EXISTE
        # ==============================================

        if not os.path.isfile(
            filepath
        ):

            message = (
                "O replay foi processado, mas o arquivo "
                "não foi encontrado: "
                + str(filepath)
            )


            if job_id:

                set_replay_job(

                    job_id,

                    "error",

                    message

                )


            return {

                "success": False,

                "message": message

            }


        # ==============================================
        # VERIFICAR TAMANHO DO ARQUIVO
        # ==============================================

        filesize = os.path.getsize(
            filepath
        )


        if filesize <= 0:

            message = (
                "O arquivo de replay foi criado vazio."
            )


            if job_id:

                set_replay_job(

                    job_id,

                    "error",

                    message

                )


            return {

                "success": False,

                "message": message

            }


        # ==============================================
        # PEGAR NOME DO ARQUIVO
        # ==============================================

        filename = os.path.basename(
            filepath
        )


        # ==============================================
        # CONECTAR AO BANCO
        # ==============================================

        conn = get_connection()

        cursor = conn.cursor()


        # ==============================================
        # HORÁRIO LOCAL DE BELÉM
        # ==============================================
        #
        # Belém está em UTC-3.
        #
        # Não usamos ZoneInfo para evitar o erro:
        #
        # No time zone found with key America/Belem
        # ==============================================

        created_at = (

            datetime.utcnow()

            - timedelta(hours=3)

        ).strftime(

            "%Y-%m-%d %H:%M:%S"

        )


        # ==============================================
        # REGISTRAR REPLAY NO BANCO
        # ==============================================

        cursor.execute(

            """
            INSERT INTO replays (

                rental_id,

                filename,

                created_at

            )
            VALUES (?, ?, ?)
            """,

            (

                rental_id,

                filename,

                created_at

            )

        )


        conn.commit()


        # ==============================================
        # MARCAR JOB COMO PRONTO
        # ==============================================

        if job_id:

            set_replay_job(

                job_id,

                "ready",

                "Replay salvo com sucesso.",

                filename

            )


        print("=" * 60)
        print("REPLAY SALVO COM SUCESSO")
        print("ARQUIVO:", filepath)
        print("TAMANHO:", filesize, "bytes")
        print("HORÁRIO:", created_at)
        print("=" * 60)


        return {

            "success": True,

            "filename": filename

        }


    except Exception as e:


        if conn is not None:

            try:

                conn.rollback()

            except Exception:

                pass


        message = str(
            e
        )


        if job_id:

            set_replay_job(

                job_id,

                "error",

                message

            )


        print("=" * 60)
        print("ERRO AO REGISTRAR/GRAVAR REPLAY")
        print(message)
        print("=" * 60)


        return {

            "success": False,

            "message": message

        }


    finally:

        if conn is not None:

            conn.close()


# ======================================================
# SALVAR REPLAY EM SEGUNDO PLANO
# ======================================================
#
# Cada solicitação possui sua própria thread.
#
# Portanto, Quadra 1 e Ping Pong 1 podem gerar
# replay ao mesmo tempo.
# ======================================================

def save_replay_background(

    rental_id,

    frames,

    job_id

):

    try:

        print("=" * 60)
        print("SALVAMENTO EM SEGUNDO PLANO")
        print("JOB ID:", job_id)
        print("RENTAL ID:", rental_id)
        print("FRAMES:", len(frames))
        print("=" * 60)


        result = save_replay_for_rental(

            rental_id,

            frames,

            job_id

        )


        if result.get(
            "success"
        ):

            print("=" * 60)
            print("REPLAY SALVO COM SUCESSO")
            print(
                "ARQUIVO:",
                result.get("filename")
            )
            print("JOB ID:", job_id)
            print("=" * 60)


        else:

            message = result.get(

                "message",

                "Falha desconhecida ao salvar o replay."

            )


            set_replay_job(

                job_id,

                "error",

                message

            )


            print("=" * 60)
            print("ERRO AO SALVAR REPLAY")
            print("JOB ID:", job_id)
            print(message)
            print("=" * 60)


    except Exception as e:

        message = str(
            e
        )


        set_replay_job(

            job_id,

            "error",

            message

        )


        print("=" * 60)
        print("ERRO NO SALVAMENTO EM SEGUNDO PLANO")
        print("JOB ID:", job_id)
        print(message)
        print("=" * 60)


# ======================================================
# SALVAR REPLAY MANUALMENTE
# ======================================================

@api_bp.route(
    "/save_replay"
)

def save_current_replay():

    frames = quadra_buffer.get_frames()


    if not frames:

        return (
            "Nenhum replay disponível."
        )


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


    return (
        "Não foi possível salvar o replay."
    )


# ======================================================
# STATUS DO SISTEMA
# ======================================================
#
# Mantido apenas para compatibilidade.
#
# NÃO EXISTE MAIS TV AO VIVO.
# ======================================================

@api_bp.route(
    "/tv/status"
)

def tv_status():

    quadra_frames = len(
        quadra_buffer.get_frames()
    )


    pingpong_frames = len(
        pingpong_buffer.get_frames()
    )


    return jsonify({

        "mode": "replay_only",

        "last_replay": None,

        "quadra_buffer_frames": quadra_frames,

        "quadra_buffer_seconds": round(

            quadra_frames / FPS,

            1

        ),

        "pingpong_buffer_frames": pingpong_frames,

        "pingpong_buffer_seconds": round(

            pingpong_frames / FPS,

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


    # ==============================================
    # RECEBER DADOS
    # ==============================================

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


    print("=" * 60)
    print("REPLAY SOLICITADO")
    print("TOKEN:", token)
    print("=" * 60)


    # ==============================================
    # BUSCAR ALUGUEL
    # ==============================================

    conn = get_connection()


    try:

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


    finally:

        conn.close()


    if rental is None:

        return jsonify({

            "success": False,

            "message": "Reserva não encontrada."

        }), 404


    rental_id = rental[
        "id"
    ]


    court = rental[
        "court"
    ]


    # ==============================================
    # ESCOLHER BUFFER CORRETO
    # ==============================================

    camera_system = CAMERA_SYSTEMS.get(
        court
    )


    if camera_system is None:

        return jsonify({

            "success": False,

            "message": (
                f"Nenhum sistema configurado para {court}."
            )

        }), 500


    buffer = camera_system.get(
        "buffer"
    )


    if buffer is None:

        return jsonify({

            "success": False,

            "message": (
                f"Nenhum buffer configurado para {court}."
            )

        }), 500


    # ==============================================
    # PEGAR FRAMES
    # ==============================================

    frames = buffer.get_frames()


    if frames is None or len(frames) == 0:

        return jsonify({

            "success": False,

            "message": (
                "Nenhum frame disponível para o replay."
            )

        }), 500


    # ==============================================
    # CRIAR JOB ID ÚNICO
    # ==============================================

    job_id = (

        str(rental_id)

        +

        "_"

        +

        str(
            int(
                time.time() * 1000
            )
        )

    )


    # ==============================================
    # CONGELAR OS FRAMES
    # ==============================================

    frozen_frames = []


    for frame in frames:

        if frame is None:

            continue


        try:

            frozen_frames.append(
                frame.copy()
            )


        except Exception:

            frozen_frames.append(
                frame
            )


    if not frozen_frames:

        return jsonify({

            "success": False,

            "message": (
                "Nenhum frame válido disponível para o replay."
            )

        }), 500


    print("=" * 60)
    print("REPLAY PREPARADO")
    print("LOCAL:", court)
    print("RENTAL ID:", rental_id)
    print("JOB ID:", job_id)
    print("FRAMES:", len(frozen_frames))
    print("=" * 60)


    # ==============================================
    # MARCAR COMO PROCESSANDO
    # ==============================================

    set_replay_job(

        job_id,

        "processing",

        "Replay está sendo gravado."

    )


    # ==============================================
    # SALVAR EM SEGUNDO PLANO
    # ==============================================

    save_thread = threading.Thread(

        target=save_replay_background,

        args=(

            rental_id,

            frozen_frames,

            job_id

        ),

        daemon=True,

        name="ReplaySave-" + job_id

    )


    save_thread.start()


    return jsonify({

        "success": True,

        "message": "Replay está sendo gravado.",

        "status": "processing",

        "job_id": job_id,

        "court": court,

        "frames": len(frozen_frames)

    })


# ======================================================
# STATUS DO REPLAY DO CLIENTE
# ======================================================

@api_bp.route(
    "/api/replay/status/<public_token>"
)

def replay_status(
    public_token
):

    conn = get_connection()

    cursor = conn.cursor()


    try:


        # ==============================================
        # BUSCAR RESERVA
        # ==============================================

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

            return jsonify({

                "success": False,

                "message": "Reserva não encontrada."

            }), 404


        # ==============================================
        # BUSCAR REPLAYS
        # ==============================================

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

                "id": replay["id"],

                "filename": replay["filename"],

                "created_at": replay["created_at"]

            })


        # ==============================================
        # DEFINIR STATUS
        # ==============================================

        if len(replays) > 0:

            replay_processing_status = "ready"

            replay_message = (
                "Replay disponível."
            )


        else:

            job_id = request.args.get(
                "job_id"
            )


            job = (

                get_replay_job(
                    job_id
                )

                if job_id

                else None

            )


            if job is not None:

                replay_processing_status = job.get(

                    "status",

                    "processing"

                )


                replay_message = job.get(

                    "message",

                    ""

                )


            else:

                replay_processing_status = (
                    "processing"
                )


                replay_message = (
                    "Replay ainda está sendo processado."
                )


        # ==============================================
        # RETORNAR STATUS
        # ==============================================

        return jsonify({

            "success": True,

            "id": rental["id"],

            "customer_name": rental["customer_name"],

            "court": rental["court"],

            "scheduled_date": rental["scheduled_date"],

            "scheduled_time": rental["scheduled_time"],

            "duration": rental["duration"],

            "status": rental["status"],

            "replay_status": replay_processing_status,

            "replay_message": replay_message,

            "public_token": rental["public_token"],

            "replays": replays

        })


    finally:

        conn.close()