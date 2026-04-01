"""File upload routes for the SkyBalance API."""

from flask import Blueprint, request
from routes import service, success_response, error_response

files_bp = Blueprint("files", __name__, url_prefix="/api")


@files_bp.route("/upload", methods=["POST"])
def upload_json():
    """
    Upload and load a JSON file.

    Expected:
    - form-data with key 'file'
    - optional query param: critical_depth

    Supports:
    - topology JSON
    - insertion JSON
    """
    try:
        if "file" not in request.files:
            return error_response("No se encontró el archivo en la petición.", 400)

        file = request.files["file"]

        if file.filename == "":
            return error_response("No se seleccionó ningún archivo.", 400)

        raw_bytes = file.read()
        critical_depth = request.args.get("critical_depth", 999, type=int)

        result = service.load_json(raw_bytes, critical_depth=critical_depth)
        return success_response(result, 200)

    except ValueError as e:
        return error_response(str(e), 400)

    except Exception as e:
        return error_response("Error al cargar el archivo: " + str(e), 500)