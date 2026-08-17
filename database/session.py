import json
import os


class Session:

    def __init__(
        self,
        token,
        customer,
        phone,
        location,
        start,
        end
    ):

        self.token = token

        self.customer = customer
        self.phone = phone

        self.location = location

        self.start = start
        self.end = end

        self.status = "waiting"

        self.replays = []

    def save(self):

        os.makedirs("storage/sessions", exist_ok=True)

        filepath = os.path.join(
            "storage",
            "sessions",
            self.token + ".json"
        )

        with open(filepath, "w", encoding="utf-8") as f:

            json.dump(
                self.__dict__,
                f,
                ensure_ascii=False,
                indent=4
            )