"""Business rule routes for the SkyBalance API."""

from flask import Blueprint, request
from routes import service, success_response, error_response

business_bp = Blueprint("business", __name__, url_prefix="/api")


@business_bp.route("/critical-depth", methods=["PUT"])
def set_critical_depth():
    """
    Update the critical depth used for price penalty calculation.

    Expected body:
    {
        "depth": 2
    }
    """
    try:
        data = request.get_json()

        if not data or "depth" not in data:
            return error_response("Falta el campo 'depth' en el body.", 400)

        result = service.set_critical_depth(data["depth"])
        return success_response(result, 200)

    except ValueError as e:
        return error_response(str(e), 400)

    except Exception as e:
        return error_response("Error al actualizar profundidad crítica: " + str(e), 500)


@business_bp.route("/eliminate-least-profitable", methods=["DELETE"])
def eliminate_least_profitable():
    """
    Eliminate the least profitable flight according to project rules.
    """
    try:
        result = service.eliminate_least_profitable()

        if "error" in result:
            return error_response(result["error"], 400)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al eliminar el vuelo menos rentable: " + str(e), 500)