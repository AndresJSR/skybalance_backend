"""Health check routes for the SkyBalance API."""

from flask import Blueprint
from routes import success_response

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Check whether the backend is running correctly.
    """
    return success_response({
        "status": "ok",
        "service": "SkyBalance Backend",
        "version": "1.0.0"
    }, 200)