import secrets
import string


ALFABETO = string.ascii_uppercase + string.digits


def generate_token(length=8):

    while True:

        token = "".join(
            secrets.choice(ALFABETO)
            for _ in range(length)
        )

        return token