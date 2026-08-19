from flask import Blueprint, send_from_directory, request, Response

import os


tv_bp = Blueprint(
    "tv",
    __name__
)


# ==========================================================
# PÁGINA DA TV
# ==========================================================

@tv_bp.route("/tv")
def tv():

    from flask import render_template

    return render_template(
        "tv.html"
    )


# ==========================================================
# SERVIR REPLAYS
# ==========================================================

@tv_bp.route("/replays/<filename>")
def replay_file(filename):

    caminho = os.path.join(
        "storage",
        "replays"
    )


    filepath = os.path.join(
        caminho,
        filename
    )


    if not os.path.isfile(filepath):

        return (
            "Replay não encontrado.",
            404
        )


    file_size = os.path.getsize(
        filepath
    )


    range_header = request.headers.get(
        "Range"
    )


    # ======================================================
    # SEM RANGE
    # ======================================================

    if not range_header:

        response = send_from_directory(

            caminho,

            filename,

            mimetype="video/mp4",

            conditional=True

        )


        response.headers[
            "Accept-Ranges"
        ] = "bytes"


        response.headers[
            "Cache-Control"
        ] = "no-cache"


        return response


    # ======================================================
    # COM RANGE
    # ======================================================

    try:

        range_value = (
            range_header
            .strip()
            .lower()
        )


        if not range_value.startswith(
            "bytes="
        ):

            return (
                "Range inválido.",
                416
            )


        range_value = range_value.replace(

            "bytes=",

            "",

            1

        )


        start_str, end_str = range_value.split(

            "-",

            1

        )


        if start_str:

            start = int(
                start_str
            )

        else:

            start = 0


        if end_str:

            end = int(
                end_str
            )

        else:

            end = (
                file_size - 1
            )


        if start >= file_size:

            return Response(

                status=416,

                headers={

                    "Content-Range":

                        f"bytes */{file_size}"

                }

            )


        if end >= file_size:

            end = (
                file_size - 1
            )


        if start > end:

            return Response(

                status=416,

                headers={

                    "Content-Range":

                        f"bytes */{file_size}"

                }

            )


        length = (

            end

            -

            start

            +

            1

        )


        with open(

            filepath,

            "rb"

        ) as video:

            video.seek(
                start
            )


            data = video.read(
                length
            )


        response = Response(

            data,

            status=206,

            mimetype="video/mp4"

        )


        response.headers[
            "Content-Range"
        ] = (

            f"bytes {start}-{end}/{file_size}"

        )


        response.headers[
            "Accept-Ranges"
        ] = "bytes"


        response.headers[
            "Content-Length"
        ] = str(
            length
        )


        response.headers[
            "Cache-Control"
        ] = "no-cache"


        return response


    except Exception as e:

        print("=" * 60)
        print("ERRO AO SERVIR REPLAY")
        print(e)
        print("=" * 60)


        return (
            "Erro ao carregar replay.",
            500
        )


# ==========================================================
# SERVIR MINIATURAS DOS REPLAYS
# ==========================================================

@tv_bp.route(
    "/replays/thumbnail/<filename>"
)
def replay_thumbnail(filename):

    caminho = os.path.join(

        "storage",

        "replays"

    )


    filepath = os.path.join(

        caminho,

        filename

    )


    if not os.path.isfile(
        filepath
    ):

        return (

            "Miniatura não encontrada.",

            404

        )


    response = send_from_directory(

        caminho,

        filename,

        mimetype="image/jpeg",

        conditional=True

    )


    response.headers[
        "Cache-Control"
    ] = "no-cache"


    return response