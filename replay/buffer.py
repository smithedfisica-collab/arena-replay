from collections import deque
import threading


class ReplayBuffer:

    def __init__(self, max_frames):

        # ==================================================
        # BUFFER CIRCULAR
        #
        # Mantém somente a quantidade máxima de frames.
        # Quando enche, o frame mais antigo é removido.
        # ==================================================

        self.buffer = deque(
            maxlen=max_frames
        )

        # ==================================================
        # PROTEÇÃO ENTRE THREADS
        # ==================================================

        self.lock = threading.Lock()


    # ======================================================
    # ADICIONAR FRAME
    # ======================================================

    def add_frame(self, frame):

        if frame is None:

            return


        with self.lock:

            # O frame recebido já vem da captura.
            # Não copiamos novamente para reduzir o uso
            # de CPU e memória.
            self.buffer.append(
                frame
            )


    # ======================================================
    # OBTER TODOS OS FRAMES
    # ======================================================

    def get_frames(self):

        with self.lock:

            # Retorna uma lista com os frames atuais.
            # Não duplica cada imagem individualmente.
            return list(
                self.buffer
            )


    # ======================================================
    # LIMPAR BUFFER
    # ======================================================

    def clear(self):

        with self.lock:

            self.buffer.clear()


    # ======================================================
    # QUANTIDADE DE FRAMES
    # ======================================================

    def __len__(self):

        with self.lock:

            return len(
                self.buffer
            )