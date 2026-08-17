from flask import Blueprint, render_template
from routes.auth import login_required

operator_bp = Blueprint("operator", __name__)


@operator_bp.route("/operator")
@login_required
def operator():

    return render_template("operator.html")