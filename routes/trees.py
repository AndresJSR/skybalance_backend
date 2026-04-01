"""Tree structure routes for the SkyBalance API."""

from flask import Blueprint, request
from routes import service, success_response, error_response

trees_bp = Blueprint("trees", __name__, url_prefix="/api")


@trees_bp.route("/trees/cancel/<code>", methods=["DELETE"])
def cancel_flight_subtree(code):
    """
    Cancel a flight and remove its full subtree.
    """
    try:
        result = service.cancel_flight(code)

        if "error" in result:
            return error_response(result["error"], 404)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al cancelar subárbol: " + str(e), 500)


@trees_bp.route("/trees/stress", methods=["POST"])
def toggle_stress_mode():
    """
    Enable or disable stress mode.

    Expected body:
    {
        "enable": true
    }
    """
    try:
        data = request.get_json()

        if not data or "enable" not in data:
            return error_response("Falta el campo 'enable' en el body.", 400)

        enable = bool(data["enable"])

        if enable:
            result = service.enable_stress_mode()
        else:
            result = service.disable_stress_mode()

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al cambiar modo estrés: " + str(e), 500)


@trees_bp.route("/trees/audit", methods=["GET"])
def audit_avl():
    """
    Audit AVL properties of the current tree.
    Only available in stress mode.
    """
    try:
        result = service.audit_avl()

        if "error" in result:
            return error_response(result["error"], 400)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error en la auditoría AVL: " + str(e), 500)


@trees_bp.route("/trees/rebalance", methods=["POST"])
def rebalance_tree():
    """
    Rebalance the tree globally.
    """
    try:
        result = service.global_rebalance()
        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al rebalancear el árbol: " + str(e), 500)