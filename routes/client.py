import json
import os

from flask import Blueprint, render_template

from database.session import Session
from database.token_generator import generate_token

session_bp = Blueprint("session", __name__)


@session_bp.route("/session/create")
def create_session():

    token = generate_token()

    sessao = Session(
        token=token,
        customer="Cliente Allan",
        phone="(91)985545986",
        location="arena",
        start="2026-08-05 21:55",
        end="2026-08-05 22:00"
    )

    sessao.save()

    return f"""
    <h2>Sessão criada!</h2>

    <p><strong>Token:</strong> {token}</p>

    <p>
    Link:<br>
    https://arenaraizes.com.br/r/{token}
</p>
    """


@session_bp.route("/r/<token>")
def client_page(token):

    filepath = os.path.join(
        "storage",
        "sessions",
        token + ".json"
    )

    if not os.path.exists(filepath):
        return "<h2>Link inválido.</h2>"

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return render_template(
        "client.html",
        session=data
    )