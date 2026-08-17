import os
import cv2
import subprocess
from datetime import datetime

import numpy as np
import imageio_ffmpeg


# ==========================================================
# CAMINHOS DO PROJETO
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

REPLAY_FOLDER = os.path.join(
    BASE_DIR,
    "storage",
    "replays"
)

LOGO_PATH = os.path.join(
    BASE_DIR,
    "static",
    "img",
    "logo.png"
)


# ==========================================================
# ADICIONAR LOGO AO FRAME
# ==========================================================

def adicionar_logo(frame, logo):

    if frame is None:
        return None

    if logo is None:
        return frame.copy()

    resultado = frame.copy()

    # Garantir BGR
    if len(resultado.shape) != 3:
        return resultado

    if resultado.shape[2] == 4:

        resultado = cv2.cvtColor(
            resultado,
            cv2.COLOR_BGRA2BGR
        )

    if resultado.shape[2] != 3:
        return resultado

    # Dimensões do frame
    altura_frame, largura_frame = resultado.shape[:2]

    # Dimensões da logo
    altura_logo, largura_logo = logo.shape[:2]

    if largura_logo <= 0 or altura_logo <= 0:
        return resultado

    # ======================================================
    # TAMANHO DA LOGO
    # ======================================================

    nova_largura = max(
        1,
        int(largura_frame * 0.18)
    )

    proporcao = (
        nova_largura /
        float(largura_logo)
    )

    nova_altura = max(
        1,
        int(altura_logo * proporcao)
    )

    # Evitar logo maior que o vídeo
    if nova_altura >= altura_frame:

        proporcao = (
            (altura_frame * 0.20) /
            float(altura_logo)
        )

        nova_largura = max(
            1,
            int(largura_logo * proporcao)
        )

        nova_altura = max(
            1,
            int(altura_logo * proporcao)
        )

    # Redimensionar
    logo_redimensionada = cv2.resize(
        logo,
        (
            nova_largura,
            nova_altura
        ),
        interpolation=cv2.INTER_AREA
    )

    # ======================================================
    # POSIÇÃO
    # CENTRALIZADA EMBAIXO
    # ======================================================

    x = int(
        (largura_frame - nova_largura) / 2
    )

    margem_inferior = max(
        10,
        int(altura_frame * 0.04)
    )

    y = (
        altura_frame
        - nova_altura
        - margem_inferior
    )

    x = max(0, x)
    y = max(0, y)

    # Garantir que fique dentro do frame
    if x + nova_largura > largura_frame:
        nova_largura = largura_frame - x

    if y + nova_altura > altura_frame:
        nova_altura = altura_frame - y

    if nova_largura <= 0 or nova_altura <= 0:
        return resultado

    # ======================================================
    # LOGO COM TRANSPARÊNCIA
    # ======================================================

    if (
        len(logo_redimensionada.shape) == 3
        and logo_redimensionada.shape[2] == 4
    ):

        logo_bgr = logo_redimensionada[:, :, :3]

        alpha = (
            logo_redimensionada[:, :, 3]
            .astype("float32")
            / 255.0
        )

        alpha = alpha[:, :, None]

        area = resultado[
            y:y + nova_altura,
            x:x + nova_largura
        ]

        mistura = (
            alpha * logo_bgr.astype("float32")
            +
            (1.0 - alpha)
            * area.astype("float32")
        )

        resultado[
            y:y + nova_altura,
            x:x + nova_largura
        ] = mistura.astype("uint8")

    # ======================================================
    # LOGO SEM TRANSPARÊNCIA
    # ======================================================

    elif (
        len(logo_redimensionada.shape) == 3
        and logo_redimensionada.shape[2] == 3
    ):

        resultado[
            y:y + nova_altura,
            x:x + nova_largura
        ] = logo_redimensionada

    return resultado


# ==========================================================
# VERIFICAR SE FRAME É BOM PARA MINIATURA
# ==========================================================

def frame_util_para_miniatura(frame):

    if frame is None:
        return False

    try:

        if len(frame.shape) != 3:
            return False

        if frame.shape[2] == 4:

            frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGRA2BGR
            )

        cinza = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        brilho_medio = float(
            np.mean(cinza)
        )

        desvio = float(
            np.std(cinza)
        )

        # Frame praticamente preto
        if brilho_medio < 12:
            return False

        # Frame sem informação visual
        if desvio < 3:
            return False

        return True

    except Exception:

        return False


# ==========================================================
# ESCOLHER MELHOR FRAME PARA MINIATURA
# ==========================================================

def escolher_frame_miniatura(frames):

    if not frames:
        return None, None

    total = len(frames)

    # Começamos pelo meio do replay
    indice_central = total // 2

    # Procurar primeiro perto do meio
    candidatos = []

    candidatos.append(indice_central)

    # Procurar para frente e para trás
    for distancia in range(1, total):

        direita = indice_central + distancia
        esquerda = indice_central - distancia

        if direita < total:
            candidatos.append(direita)

        if esquerda >= 0:
            candidatos.append(esquerda)

    # Encontrar o primeiro frame visualmente bom
    for indice in candidatos:

        frame = frames[indice]

        if frame_util_para_miniatura(frame):

            return frame.copy(), indice

    # Se nenhum passar no teste,
    # usar o frame do meio mesmo
    frame = frames[indice_central]

    if frame is not None:
        return frame.copy(), indice_central

    # Última tentativa
    for indice, frame in enumerate(frames):

        if frame is not None:
            return frame.copy(), indice

    return None, None


# ==========================================================
# SALVAR IMAGEM COM SUPORTE A CAMINHOS DO WINDOWS
# ==========================================================

def salvar_imagem(caminho, imagem):

    try:

        extensao = os.path.splitext(
            caminho
        )[1]

        if not extensao:
            extensao = ".jpg"

        sucesso, buffer = cv2.imencode(
            extensao,
            imagem
        )

        if not sucesso:
            return False

        buffer.tofile(
            caminho
        )

        return os.path.isfile(caminho)

    except Exception as e:

        print(
            "ERRO AO SALVAR IMAGEM:",
            e
        )

        return False


# ==========================================================
# SALVAR REPLAY
# ==========================================================

def save_replay(frames, fps=30):

    print("=" * 60)
    print("SAVE_REPLAY INICIADO")
    print("ARQUIVO EXECUTADO:")
    print(__file__)
    print("=" * 60)

    # ======================================================
    # VERIFICAR FRAMES
    # ======================================================

    if not frames:

        print(
            "ERRO: Nenhum frame recebido."
        )

        return None

    # ======================================================
    # REMOVER FRAMES VAZIOS
    # ======================================================

    frames_validos = []

    for frame in frames:

        if frame is not None:

            frames_validos.append(
                frame
            )

    if not frames_validos:

        print(
            "ERRO: Todos os frames estão vazios."
        )

        return None

    # ======================================================
    # PRIMEIRO FRAME
    # ======================================================

    primeiro_frame = frames_validos[0]

    if primeiro_frame is None:

        print(
            "ERRO: Primeiro frame inválido."
        )

        return None

    # Garantir BGR
    if (
        len(primeiro_frame.shape) == 3
        and primeiro_frame.shape[2] == 4
    ):

        primeiro_frame = cv2.cvtColor(
            primeiro_frame,
            cv2.COLOR_BGRA2BGR
        )

    if len(primeiro_frame.shape) != 3:

        print(
            "ERRO: Formato do frame inválido."
        )

        return None

    altura, largura = primeiro_frame.shape[:2]

    # ======================================================
    # CRIAR PASTA
    # ======================================================

    os.makedirs(
        REPLAY_FOLDER,
        exist_ok=True
    )

    # ======================================================
    # NOME DO REPLAY
    # ======================================================

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        timestamp
        + ".mp4"
    )

    thumbnail_filename = (
        timestamp
        + ".jpg"
    )

    filepath = os.path.join(
        REPLAY_FOLDER,
        filename
    )

    thumbnail_path = os.path.join(
        REPLAY_FOLDER,
        thumbnail_filename
    )

    # ======================================================
    # INFORMAÇÕES
    # ======================================================

    print("=" * 60)
    print("SALVANDO REPLAY")
    print("REPLAY:")
    print(filepath)

    print()
    print("MINIATURA:")
    print(thumbnail_path)

    print()
    print("LOGO:")
    print(LOGO_PATH)

    print()
    print(
        "LOGO EXISTE:",
        os.path.isfile(LOGO_PATH)
    )

    print()
    print(
        "FRAMES:",
        len(frames_validos)
    )

    print()
    print(
        "DIMENSÃO:",
        largura,
        "x",
        altura
    )

    print()
    print(
        "FPS:",
        fps
    )

    print("=" * 60)

    # ======================================================
    # VERIFICAR LOGO
    # ======================================================

    if not os.path.isfile(LOGO_PATH):

        print("=" * 60)
        print("ERRO: LOGO NÃO ENCONTRADA")
        print(LOGO_PATH)
        print("=" * 60)

        return None

    # ======================================================
    # CARREGAR LOGO
    # ======================================================

    try:

        logo = cv2.imdecode(
            np.fromfile(
                LOGO_PATH,
                dtype=np.uint8
            ),
            cv2.IMREAD_UNCHANGED
        )

    except Exception as e:

        print("=" * 60)
        print("ERRO AO CARREGAR A LOGO:")
        print(e)
        print("=" * 60)

        return None

    if logo is None:

        print("=" * 60)
        print(
            "ERRO: NÃO FOI POSSÍVEL CARREGAR A LOGO."
        )
        print("=" * 60)

        return None

    print("=" * 60)
    print("LOGO CARREGADA COM SUCESSO")
    print(
        "DIMENSÃO:",
        logo.shape
    )
    print("=" * 60)

    # ======================================================
    # ESCOLHER FRAME DA MINIATURA
    # ======================================================

    frame_miniatura, indice_miniatura = (
        escolher_frame_miniatura(
            frames_validos
        )
    )

    if frame_miniatura is None:

        print(
            "AVISO: NÃO FOI POSSÍVEL ESCOLHER FRAME PARA MINIATURA."
        )

    else:

        print("=" * 60)
        print("FRAME ESCOLHIDO PARA A MINIATURA:")
        print(indice_miniatura)
        print("=" * 60)

        # Garantir tamanho correto
        if (
            frame_miniatura.shape[0] != altura
            or frame_miniatura.shape[1] != largura
        ):

            frame_miniatura = cv2.resize(
                frame_miniatura,
                (
                    largura,
                    altura
                )
            )

        # Garantir BGR
        if (
            len(frame_miniatura.shape) == 3
            and frame_miniatura.shape[2] == 4
        ):

            frame_miniatura = cv2.cvtColor(
                frame_miniatura,
                cv2.COLOR_BGRA2BGR
            )

        # APLICAR LOGO À MINIATURA
        miniatura_com_logo = adicionar_logo(
            frame_miniatura,
            logo
        )

        if miniatura_com_logo is not None:

            sucesso_miniatura = salvar_imagem(
                thumbnail_path,
                miniatura_com_logo
            )

            if sucesso_miniatura:

                print("=" * 60)
                print("MINIATURA CRIADA COM SUCESSO!")
                print(thumbnail_path)
                print("=" * 60)

            else:

                print("=" * 60)
                print(
                    "AVISO: NÃO FOI POSSÍVEL CRIAR A MINIATURA."
                )
                print("=" * 60)

    # ======================================================
    # LOCALIZAR FFMPEG
    # ======================================================

    try:

        ffmpeg_exe = (
            imageio_ffmpeg.get_ffmpeg_exe()
        )

    except Exception as e:

        print("=" * 60)
        print("ERRO AO LOCALIZAR O FFMPEG")
        print(e)
        print("=" * 60)

        return None

    print("=" * 60)
    print("FFMPEG:")
    print(ffmpeg_exe)
    print("=" * 60)

    # ======================================================
    # COMANDO FFMPEG
    # ======================================================

    comando = [

        ffmpeg_exe,

        "-y",

        "-f",
        "rawvideo",

        "-vcodec",
        "rawvideo",

        "-pix_fmt",
        "rgb24",

        "-s",
        f"{largura}x{altura}",

        "-r",
        str(fps),

        "-i",
        "-",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        filepath
    ]

    # ======================================================
    # INICIAR FFMPEG
    # ======================================================

    processo = None

    try:

        processo = subprocess.Popen(

            comando,

            stdin=subprocess.PIPE,

            stdout=subprocess.DEVNULL,

            stderr=subprocess.PIPE
        )

        frames_enviados = 0

        # ==================================================
        # PROCESSAR FRAMES
        # ==================================================

        for indice, frame in enumerate(
            frames_validos
        ):

            if frame is None:
                continue

            # Garantir tamanho
            if (
                frame.shape[0] != altura
                or frame.shape[1] != largura
            ):

                frame = cv2.resize(
                    frame,
                    (
                        largura,
                        altura
                    )
                )

            # Garantir BGR
            if (
                len(frame.shape) == 3
                and frame.shape[2] == 4
            ):

                frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGRA2BGR
                )

            # Aplicar logo
            frame_com_logo = adicionar_logo(
                frame,
                logo
            )

            if frame_com_logo is None:
                continue

            # Converter BGR para RGB
            frame_rgb = cv2.cvtColor(
                frame_com_logo,
                cv2.COLOR_BGR2RGB
            )

            # Enviar ao FFMPEG
            processo.stdin.write(
                frame_rgb.tobytes()
            )

            frames_enviados += 1

        # ==================================================
        # FECHAR ENTRADA
        # ==================================================

        processo.stdin.close()

        print("=" * 60)
        print(
            "FRAMES COM LOGO ENVIADOS AO FFMPEG:"
        )
        print(
            frames_enviados
        )
        print("=" * 60)

        # ==================================================
        # LER RESULTADO
        # ==================================================

        erro_ffmpeg = processo.stderr.read()

        retorno = processo.wait()

        # ==================================================
        # VERIFICAR ERRO
        # ==================================================

        if retorno != 0:

            print("=" * 60)
            print(
                "ERRO AO GERAR O MP4"
            )

            print(
                "CÓDIGO:",
                retorno
            )

            print("=" * 60)

            try:

                print(
                    erro_ffmpeg.decode(
                        "utf-8",
                        errors="ignore"
                    )
                )

            except Exception:

                pass

            return None

    except Exception as e:

        print("=" * 60)
        print(
            "ERRO AO SALVAR REPLAY"
        )
        print(e)
        print("=" * 60)

        if processo is not None:

            try:

                processo.kill()

            except Exception:

                pass

        return None

    # ======================================================
    # VERIFICAR ARQUIVO
    # ======================================================

    if not os.path.exists(filepath):

        print("=" * 60)
        print(
            "ERRO: O MP4 NÃO FOI CRIADO."
        )
        print("=" * 60)

        return None

    tamanho = os.path.getsize(
        filepath
    )

    if tamanho <= 0:

        print("=" * 60)
        print(
            "ERRO: O MP4 ESTÁ VAZIO."
        )
        print("=" * 60)

        return None

    # ======================================================
    # VERIFICAR MINIATURA
    # ======================================================

    if os.path.exists(thumbnail_path):

        tamanho_miniatura = os.path.getsize(
            thumbnail_path
        )

        print(
            "MINIATURA:",
            thumbnail_filename
        )

        print(
            "TAMANHO DA MINIATURA:",
            tamanho_miniatura,
            "bytes"
        )

    else:

        print(
            "AVISO: REPLAY SALVO, MAS A MINIATURA NÃO FOI ENCONTRADA."
        )

    # ======================================================
    # FINAL
    # ======================================================

    print("=" * 60)
    print(
        "REPLAY SALVO COM SUCESSO!"
    )

    print(
        "ARQUIVO:",
        filename
    )

    print(
        "TAMANHO:",
        tamanho,
        "bytes"
    )

    print(
        "A LOGO FOI APLICADA AOS FRAMES."
    )

    print("=" * 60)

    return filepath