"""Metrics routes for the SkyBalance API."""

from flask import Blueprint
from routes import service, success_response, error_response

metrics_bp = Blueprint("metrics", __name__, url_prefix="/api")


@metrics_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Return all current tree metrics and traversals.
    """
    try:
        result = service.get_metrics()
        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al obtener métricas: " + str(e), 500)