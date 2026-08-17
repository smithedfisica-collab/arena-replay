import cv2
import time
import threading
import os
from urllib.parse import quote


class Camera:

    def __init__(self):

        # ==================================================
        # CONFIGURAÇÕES GERAIS
        # ==================================================

        self.usuario = "admin"
        self.senha = "@Mith00lima2A"

        senha_codificada = quote(
            self.senha,
            safe=""
        )

        # ==================================================
        # CÂMERA 1 — QUADRA 1
        # ==================================================

        self.quadra_ip = "192.168.1.2"

        # STREAM 2
        #
        # Por enquanto será usado tanto no AO VIVO
        # quanto no REPLAY para diminuir o peso
        # sobre o processador.
        self.quadra_live_url = (
            f"rtsp://{self.usuario}:"
            f"{senha_codificada}"
            f"@{self.quadra_ip}:554/stream2"
        )

        self.quadra_replay_url = (
            f"rtsp://{self.usuario}:"
            f"{senha_codificada}"
            f"@{self.quadra_ip}:554/stream2"
        )


        # ==================================================
        # CÂMERA 2 — PING PONG 1
        # ==================================================

        self.pingpong_ip = "192.168.1.118"

        # STREAM 2
        #
        # Usado somente para capturar o replay.
        # Não será enviado ao vivo para a TV.
        self.pingpong_replay_url = (
            f"rtsp://{self.usuario}:"
            f"{senha_codificada}"
            f"@{self.pingpong_ip}:554/stream2"
        )


        # ==================================================
        # CONFIGURAÇÕES FFMPEG
        #
        # FOCO:
        # MENOR ATRASO + MENOS BUFFER
        # ==================================================

        os.environ[
            "OPENCV_FFMPEG_CAPTURE_OPTIONS"
        ] = (
            "rtsp_transport;udp|"
            "fflags;nobuffer|"
            "flags;low_delay|"
            "max_delay;0"
        )


        # ==================================================
        # CONTROLE GERAL
        # ==================================================

        self.running = True


        # ==================================================
        # QUADRA 1 — AO VIVO
        # ==================================================

        self.live_camera = None

        self.live_frame = None

        self.live_lock = threading.Lock()

        self.live_connected = False


        # ==================================================
        # QUADRA 1 — REPLAY
        # ==================================================

        self.replay_camera = None

        self.replay_frame = None

        self.replay_lock = threading.Lock()

        self.replay_connected = False

        self.replay_sequence = 0


        # ==================================================
        # PING PONG 1 — REPLAY
        # ==================================================

        self.pingpong_camera = None

        self.pingpong_frame = None

        self.pingpong_lock = threading.Lock()

        self.pingpong_connected = False

        self.pingpong_sequence = 0


        print("=" * 60)
        print("INICIANDO SISTEMA DE CÂMERAS")
        print("=" * 60)

        print()
        print("CÂMERA 1 — QUADRA 1")
        print(f"IP: {self.quadra_ip}")
        print("AO VIVO: STREAM 2")
        print("REPLAY: STREAM 2")

        print()
        print("CÂMERA 2 — PING PONG 1")
        print(f"IP: {self.pingpong_ip}")
        print("REPLAY: STREAM 2")

        print()
        print("TV AO VIVO: QUADRA 1")
        print("=" * 60)


        # ==================================================
        # THREAD — AO VIVO QUADRA 1
        # ==================================================

        self.live_thread = threading.Thread(
            target=self._live_capture_loop,
            daemon=True
        )


        # ==================================================
        # THREAD — REPLAY QUADRA 1
        # ==================================================

        self.replay_thread = threading.Thread(
            target=self._replay_capture_loop,
            daemon=True
        )


        # ==================================================
        # THREAD — REPLAY PING PONG 1
        # ==================================================

        self.pingpong_thread = threading.Thread(
            target=self._pingpong_capture_loop,
            daemon=True
        )


        # ==================================================
        # INICIA TODAS AS CAPTURAS
        # ==================================================

        self.live_thread.start()

        self.replay_thread.start()

        self.pingpong_thread.start()


    # ======================================================
    # CONECTAR AO VIVO — QUADRA 1
    # ======================================================

    def _connect_live(self):

        print("=" * 60)
        print("CONECTANDO AO VIVO DA QUADRA 1...")
        print("STREAM 2")
        print("=" * 60)

        if self.live_camera is not None:

            try:
                self.live_camera.release()
            except Exception:
                pass

            self.live_camera = None


        self.live_camera = cv2.VideoCapture(
            self.quadra_live_url,
            cv2.CAP_FFMPEG
        )


        try:

            self.live_camera.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

        except Exception:
            pass


        if not self.live_camera.isOpened():

            print("ERRO AO CONECTAR AO VIVO DA QUADRA 1")

            self.live_connected = False

            try:
                self.live_camera.release()
            except Exception:
                pass

            self.live_camera = None

            return False


        self.live_connected = True

        print("AO VIVO DA QUADRA 1 CONECTADO!")

        return True


    # ======================================================
    # CONECTAR REPLAY — QUADRA 1
    # ======================================================

    def _connect_replay(self):

        print("=" * 60)
        print("CONECTANDO REPLAY DA QUADRA 1...")
        print("STREAM 2")
        print("=" * 60)

        if self.replay_camera is not None:

            try:
                self.replay_camera.release()
            except Exception:
                pass

            self.replay_camera = None


        self.replay_camera = cv2.VideoCapture(
            self.quadra_replay_url,
            cv2.CAP_FFMPEG
        )


        try:

            self.replay_camera.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

        except Exception:
            pass


        if not self.replay_camera.isOpened():

            print("ERRO AO CONECTAR REPLAY DA QUADRA 1")

            self.replay_connected = False

            try:
                self.replay_camera.release()
            except Exception:
                pass

            self.replay_camera = None

            return False


        self.replay_connected = True

        print("REPLAY DA QUADRA 1 CONECTADO!")

        return True


    # ======================================================
    # CONECTAR REPLAY — PING PONG 1
    # ======================================================

    def _connect_pingpong(self):

        print("=" * 60)
        print("CONECTANDO REPLAY DO PING PONG 1...")
        print(f"IP: {self.pingpong_ip}")
        print("STREAM 2")
        print("=" * 60)

        if self.pingpong_camera is not None:

            try:
                self.pingpong_camera.release()
            except Exception:
                pass

            self.pingpong_camera = None


        self.pingpong_camera = cv2.VideoCapture(
            self.pingpong_replay_url,
            cv2.CAP_FFMPEG
        )


        try:

            self.pingpong_camera.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

        except Exception:
            pass


        if not self.pingpong_camera.isOpened():

            print("ERRO AO CONECTAR PING PONG 1")

            self.pingpong_connected = False

            try:
                self.pingpong_camera.release()
            except Exception:
                pass

            self.pingpong_camera = None

            return False


        self.pingpong_connected = True

        print("REPLAY DO PING PONG 1 CONECTADO!")

        return True


    # ======================================================
    # THREAD — AO VIVO QUADRA 1
    # ======================================================

    def _live_capture_loop(self):

        print("=" * 60)
        print("THREAD AO VIVO DA QUADRA 1 INICIADA")
        print("=" * 60)


        while self.running:

            try:

                if (
                    self.live_camera is None
                    or
                    not self.live_camera.isOpened()
                ):

                    if not self._connect_live():

                        time.sleep(1)

                        continue


                success, frame = self.live_camera.read()


                if not success or frame is None:

                    print(
                        "FALHA NO AO VIVO DA QUADRA."
                        " RECONECTANDO..."
                    )

                    self.live_connected = False


                    try:
                        self.live_camera.release()
                    except Exception:
                        pass


                    self.live_camera = None

                    time.sleep(0.3)

                    continue


                # Mantém somente o frame mais recente

                with self.live_lock:

                    self.live_frame = frame


            except Exception as e:

                print("=" * 60)
                print("ERRO NO AO VIVO DA QUADRA")
                print(e)
                print("=" * 60)

                self.live_connected = False


                try:

                    if self.live_camera is not None:

                        self.live_camera.release()

                except Exception:
                    pass


                self.live_camera = None

                time.sleep(0.5)


    # ======================================================
    # THREAD — REPLAY QUADRA 1
    # ======================================================

    def _replay_capture_loop(self):

        print("=" * 60)
        print("THREAD REPLAY DA QUADRA 1 INICIADA")
        print("STREAM 2")
        print("=" * 60)


        while self.running:

            try:

                if (
                    self.replay_camera is None
                    or
                    not self.replay_camera.isOpened()
                ):

                    if not self._connect_replay():

                        time.sleep(1)

                        continue


                success, frame = self.replay_camera.read()


                if not success or frame is None:

                    print(
                        "FALHA NO REPLAY DA QUADRA."
                        " RECONECTANDO..."
                    )

                    self.replay_connected = False


                    try:
                        self.replay_camera.release()
                    except Exception:
                        pass


                    self.replay_camera = None

                    time.sleep(0.3)

                    continue


                with self.replay_lock:

                    self.replay_frame = frame

                    self.replay_sequence += 1


            except Exception as e:

                print("=" * 60)
                print("ERRO NO REPLAY DA QUADRA")
                print(e)
                print("=" * 60)

                self.replay_connected = False


                try:

                    if self.replay_camera is not None:

                        self.replay_camera.release()

                except Exception:
                    pass


                self.replay_camera = None

                time.sleep(0.5)


    # ======================================================
    # THREAD — REPLAY PING PONG 1
    # ======================================================

    def _pingpong_capture_loop(self):

        print("=" * 60)
        print("THREAD REPLAY DO PING PONG 1 INICIADA")
        print("STREAM 2")
        print("=" * 60)


        while self.running:

            try:

                if (
                    self.pingpong_camera is None
                    or
                    not self.pingpong_camera.isOpened()
                ):

                    if not self._connect_pingpong():

                        time.sleep(1)

                        continue


                success, frame = self.pingpong_camera.read()


                if not success or frame is None:

                    print(
                        "FALHA NO REPLAY DO PING PONG."
                        " RECONECTANDO..."
                    )

                    self.pingpong_connected = False


                    try:
                        self.pingpong_camera.release()
                    except Exception:
                        pass


                    self.pingpong_camera = None

                    time.sleep(0.3)

                    continue


                with self.pingpong_lock:

                    self.pingpong_frame = frame

                    self.pingpong_sequence += 1


            except Exception as e:

                print("=" * 60)
                print("ERRO NO REPLAY DO PING PONG")
                print(e)
                print("=" * 60)

                self.pingpong_connected = False


                try:

                    if self.pingpong_camera is not None:

                        self.pingpong_camera.release()

                except Exception:
                    pass


                self.pingpong_camera = None

                time.sleep(0.5)


    # ======================================================
    # RETORNA FRAME AO VIVO PARA TV
    #
    # QUADRA 1
    # ======================================================

    def get_frame(self):

        with self.live_lock:

            if self.live_frame is None:

                return None


            return self.live_frame.copy()


    # ======================================================
    # RETORNA FRAME PARA REPLAY
    #
    # QUADRA 1
    # ======================================================

    def get_replay_frame(self):

        with self.replay_lock:

            if self.replay_frame is None:

                return None


            return self.replay_frame.copy()


    # ======================================================
    # RETORNA FRAME + SEQUÊNCIA
    #
    # QUADRA 1
    # ======================================================

    def get_replay_frame_with_sequence(self):

        with self.replay_lock:

            if self.replay_frame is None:

                return (
                    None,
                    self.replay_sequence
                )


            return (
                self.replay_frame.copy(),
                self.replay_sequence
            )


    # ======================================================
    # RETORNA FRAME PARA REPLAY
    #
    # PING PONG 1
    # ======================================================

    def get_pingpong_frame(self):

        with self.pingpong_lock:

            if self.pingpong_frame is None:

                return None


            return self.pingpong_frame.copy()


    # ======================================================
    # RETORNA FRAME + SEQUÊNCIA
    #
    # PING PONG 1
    # ======================================================

    def get_pingpong_frame_with_sequence(self):

        with self.pingpong_lock:

            if self.pingpong_frame is None:

                return (
                    None,
                    self.pingpong_sequence
                )


            return (
                self.pingpong_frame.copy(),
                self.pingpong_sequence
            )


    # ======================================================
    # STATUS DAS CÂMERAS
    # ======================================================

    def get_status(self):

        return {

            "live_connected":
                self.live_connected,

            "replay_connected":
                self.replay_connected,

            "pingpong_connected":
                self.pingpong_connected

        }


    # ======================================================
    # DESCONECTAR TODAS AS CÂMERAS
    # ======================================================

    def release(self):

        print("=" * 60)
        print("ENCERRANDO CÂMERAS...")
        print("=" * 60)


        self.running = False


        # Aguarda as threads terminarem

        try:

            if (
                self.live_thread.is_alive()
                and
                threading.current_thread()
                != self.live_thread
            ):

                self.live_thread.join(
                    timeout=1
                )

        except Exception:
            pass


        try:

            if (
                self.replay_thread.is_alive()
                and
                threading.current_thread()
                != self.replay_thread
            ):

                self.replay_thread.join(
                    timeout=1
                )

        except Exception:
            pass


        try:

            if (
                self.pingpong_thread.is_alive()
                and
                threading.current_thread()
                != self.pingpong_thread
            ):

                self.pingpong_thread.join(
                    timeout=1
                )

        except Exception:
            pass


        # Fecha câmera ao vivo

        if self.live_camera is not None:

            try:
                self.live_camera.release()
            except Exception:
                pass

            self.live_camera = None


        # Fecha replay Quadra

        if self.replay_camera is not None:

            try:
                self.replay_camera.release()
            except Exception:
                pass

            self.replay_camera = None


        # Fecha replay Ping Pong

        if self.pingpong_camera is not None:

            try:
                self.pingpong_camera.release()
            except Exception:
                pass

            self.pingpong_camera = None


        self.live_connected = False

        self.replay_connected = False

        self.pingpong_connected = False


        # Limpa os últimos frames

        with self.live_lock:

            self.live_frame = None


        with self.replay_lock:

            self.replay_frame = None


        with self.pingpong_lock:

            self.pingpong_frame = None


        print("TODAS AS CÂMERAS DESCONECTADAS.")