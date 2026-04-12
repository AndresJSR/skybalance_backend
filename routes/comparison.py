"""Comparative AVL vs BST routes for the SkyBalance API."""

from flask import Blueprint
from routes import service, success_response, error_response

comparison_bp = Blueprint("comparison", __name__, url_prefix="/api")


@comparison_bp.route("/trees/comparison/current", methods=["GET"])
@comparison_bp.route("/compare/current", methods=["GET"])
def get_current_comparison():
    """
    Return the current comparative snapshot for AVL and BST.
    """
    try:
        result = service.get_comparative_snapshot()
        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al obtener comparativa actual: " + str(e), 500)
