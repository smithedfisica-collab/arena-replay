from flask import Flask, redirect
from datetime import timedelta, datetime

from config import SECRET_KEY, SESSION_HOURS

from database.init_database import init_database

from routes.dashboard import dashboard_bp
from routes.operator import operator_bp
from routes.tv import tv_bp
from routes.api import api_bp
from routes.login import login_bp
from routes.rentals import rentals_bp


# ==========================================================
# INICIALIZAR BANCO DE DADOS
# ==========================================================

init_database()


# ==========================================================
# CRIAÇÃO DO APP
# ==========================================================

app = Flask(__name__)


# ==========================================================
# FILTRO PARA MOSTRAR O DIA DA SEMANA
# ==========================================================

@app.template_filter("weekday")
def weekday_filter(date_string):

    try:

        date = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        )

        weekdays = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo"
        ]

        return weekdays[date.weekday()]

    except Exception:

        return ""


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

app.secret_key = SECRET_KEY

app.permanent_session_lifetime = timedelta(
    hours=SESSION_HOURS
)


# ==========================================================
# PÁGINA INICIAL
# ==========================================================

@app.route("/")
def home():

    return redirect("/dashboard")


# ==========================================================
# BLUEPRINTS
# ==========================================================

app.register_blueprint(login_bp)

app.register_blueprint(dashboard_bp)

app.register_blueprint(operator_bp)

app.register_blueprint(tv_bp)

app.register_blueprint(api_bp)

app.register_blueprint(rentals_bp)


# ==========================================================
# EXECUÇÃO
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=False
    )