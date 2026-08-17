import os
import shutil

from flask import Blueprint, render_template
from routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    # ==========================================
    # CÂMERAS ONLINE
    # ==========================================

    cameras_online = 0

    try:

        from camera.camera import camera_manager

        cameras_online = camera_manager.get_online_cameras_count()

    except Exception as e:

        print("Erro ao verificar câmeras:", e)


    # ==========================================
    # QUANTIDADE DE REPLAYS
    # ==========================================

    replays_count = 0

    try:

        replay_folder = "replays"

        if os.path.exists(replay_folder):

            arquivos = [
                arquivo
                for arquivo in os.listdir(replay_folder)
                if arquivo.lower().endswith(
                    (
                        ".mp4",
                        ".avi",
                        ".mov"
                    )
                )
            ]

            replays_count = len(arquivos)

    except Exception as e:

        print("Erro ao contar replays:", e)


    # ==========================================
    # ESPAÇO DISPONÍVEL
    # ==========================================

    free_space_gb = 0

    try:

        total, used, free = shutil.disk_usage(
            os.getcwd()
        )

        free_space_gb = round(
            free / (1024 ** 3)
        )

    except Exception as e:

        print("Erro ao verificar espaço:", e)


    # ==========================================
    # TEMPO DO BUFFER
    # ==========================================

    buffer_seconds = 20


    # ==========================================
    # RENDERIZA DASHBOARD
    # ==========================================

    return render_template(

        "dashboard.html",

        cameras_online=cameras_online,

        replays_count=replays_count,

        free_space_gb=free_space_gb,

        buffer_seconds=buffer_seconds

    )