"""Export routes for the SkyBalance API."""

import json
from flask import Blueprint
from routes import service, success_response, error_response

export_bp = Blueprint("export", __name__, url_prefix="/api")


@export_bp.route("/export", methods=["GET"])
def export_tree():
    """
    Export the current AVL tree as structured JSON.
    """
    try:
        json_text = service.export_json_text()
        tree_data = json.loads(json_text)

        return success_response({
            "tree": tree_data
        }, 200)

    except Exception as e:
        return error_response("Error al exportar el árbol: " + str(e), 500)