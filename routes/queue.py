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


@queue_bp.route("/queue/simulations/start", methods=["POST"])
def start_parallel_simulation():
    """
    Start a parallel insertion simulation using N workers.

    Expected body (all optional):
    {
        "workers": 3,
        "maxItems": 20,
        "delayMs": 100
    }
    """
    try:
        data = request.get_json(silent=True) or {}

        workers = data.get("workers", 2)
        max_items = data.get("maxItems")
        delay_ms = data.get("delayMs", 0)

        result = service.start_parallel_queue_simulation(
            workers=workers,
            max_items=max_items,
            delay_ms=delay_ms,
        )

        if "error" in result:
            return error_response(result["error"], 400)

        return success_response(result, 202)

    except ValueError as e:
        return error_response(str(e), 400)

    except Exception as e:
        return error_response("Error al iniciar simulación paralela: " + str(e), 500)


@queue_bp.route("/queue/simulations/<job_id>", methods=["GET"])
def get_parallel_simulation_status(job_id):
    """
    Get the current status for a parallel insertion simulation.
    """
    try:
        result = service.get_parallel_simulation_status(job_id)

        if "error" in result:
            return error_response(result["error"], 404)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al consultar simulación paralela: " + str(e), 500)


@queue_bp.route("/queue/simulations/<job_id>/events", methods=["GET"])
def get_parallel_simulation_events(job_id):
    """
    Get paginated simulation events for a parallel insertion job.
    Query params:
    - offset (default 0)
    - limit (default 100)
    """
    try:
        offset = request.args.get("offset", 0, type=int)
        limit = request.args.get("limit", 100, type=int)

        result = service.list_parallel_simulation_events(job_id, offset=offset, limit=limit)

        if "error" in result:
            status = 404 if result["error"] == "La simulación no existe." else 400
            return error_response(result["error"], status)

        return success_response(result, 200)

    except ValueError as e:
        return error_response(str(e), 400)

    except Exception as e:
        return error_response("Error al obtener eventos de simulación: " + str(e), 500)


@queue_bp.route("/queue/simulations/<job_id>/stop", methods=["POST"])
def stop_parallel_simulation(job_id):
    """
    Request a running simulation to stop.
    """
    try:
        result = service.stop_parallel_queue_simulation(job_id)

        if "error" in result:
            status = 404 if result["error"] == "La simulación no existe." else 400
            return error_response(result["error"], status)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al detener simulación paralela: " + str(e), 500)