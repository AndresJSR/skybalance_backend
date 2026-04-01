"""Undo routes for the SkyBalance API."""

from flask import Blueprint
from routes import service, success_response, error_response

undo_bp = Blueprint("undo", __name__, url_prefix="/api")


@undo_bp.route("/undo", methods=["POST"])
def undo_last_action():
    """
    Undo the last mutating action on the tree.
    """
    try:
        result = service.undo()

        if "error" in result:
            return error_response(result["error"], 400)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al deshacer la última acción: " + str(e), 500)