"""Queue routes for the SkyBalance API."""

from flask import Blueprint, request
from routes import service, success_response, error_response

queue_bp = Blueprint("queue", __name__, url_prefix="/api")


@queue_bp.route("/queue", methods=["GET"])
def list_queue():
    """
    Return the current insertion queue.
    """
    try:
        result = service.list_queue()
        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al listar la cola: " + str(e), 500)


@queue_bp.route("/queue", methods=["POST"])
def enqueue_flight():
    """
    Add a flight to the insertion queue.
    """
    try:
        data = request.get_json()

        if not data:
            return error_response("Body vacío o inválido.", 400)

        result = service.enqueue_flight(data)
        return success_response(result, 201)

    except Exception as e:
        return error_response("Error al encolar vuelo: " + str(e), 500)


@queue_bp.route("/queue/process", methods=["POST"])
def process_next_queue():
    """
    Process the next pending flight in the queue.
    """
    try:
        result = service.process_next_in_queue()

        if "error" in result:
            return error_response(result["error"], 400)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al procesar siguiente elemento de la cola: " + str(e), 500)


@queue_bp.route("/queue/process-all", methods=["POST"])
def process_all_queue():
    """
    Process all pending flights in the queue.
    """
    try:
        result = service.process_full_queue()
        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al procesar toda la cola: " + str(e), 500)


@queue_bp.route("/queue/<code>", methods=["DELETE"])
def remove_from_queue(code):
    """
    Remove a specific flight from the queue by code.
    """
    try:
        result = service.remove_from_queue(code)

        if "error" in result:
            return error_response(result["error"], 404)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al eliminar de la cola: " + str(e), 500)