from flask import Blueprint, render_template, request, redirect, session

from config import ADMIN_USER, ADMIN_PASSWORD

login_bp = Blueprint("login", __name__)


@login_bp.route("/login", methods=["GET", "POST"])
def login():

    if session.get("logged"):
        return redirect("/dashboard")

    if request.method == "POST":

        usuario = request.form["usuario"]
        senha = request.form["senha"]

        if usuario == ADMIN_USER and senha == ADMIN_PASSWORD:

            session["logged"] = True
            session["user"] = "Allan Smith"
            session["role"] = "Administrador"

            session.permanent = True

            return redirect("/dashboard")

        return render_template(
            "login.html",
            erro="Usuário ou senha incorretos."
        )

    return render_template("login.html")


@login_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/login")