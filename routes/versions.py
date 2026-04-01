"""Version routes for the SkyBalance API."""

from flask import Blueprint
from routes import service, success_response, error_response

versions_bp = Blueprint("versions", __name__, url_prefix="/api")


@versions_bp.route("/versions", methods=["GET"])
def list_versions():
    """
    Return all saved version names.
    """
    try:
        versions = service.list_versions()
        return success_response({"versions": versions}, 200)

    except Exception as e:
        return error_response("Error al listar versiones: " + str(e), 500)


@versions_bp.route("/versions/<name>", methods=["POST"])
def save_version(name):
    """
    Save the current tree state under a given name.
    """
    try:
        result = service.save_version(name)
        return success_response(result, 201)

    except Exception as e:
        return error_response("Error al guardar versión: " + str(e), 500)


@versions_bp.route("/versions/<name>", methods=["PUT"])
def restore_version(name):
    """
    Restore a previously saved version.
    """
    try:
        result = service.restore_version(name)

        if "error" in result:
            return error_response(result["error"], 404)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al restaurar versión: " + str(e), 500)


@versions_bp.route("/versions/<name>", methods=["DELETE"])
def delete_version(name):
    """
    Delete a saved version by name.
    """
    try:
        result = service.delete_version(name)

        if "error" in result:
            return error_response(result["error"], 404)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al eliminar versión: " + str(e), 500)