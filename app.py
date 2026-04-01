"""SkyBalance Backend - Flask application entry point."""

from flask import Flask
from flask_cors import CORS

from routes.health import health_bp
from routes.files import files_bp
from routes.flights_routes import flights_bp
from routes.trees import trees_bp
from routes.queue import queue_bp
from routes.versions import versions_bp
from routes.metrics import metrics_bp
from routes.export import export_bp
from routes.undo import undo_bp
from routes.business import business_bp


def create_app():
    """
    Create and configure the Flask application.
    """
    app = Flask(__name__)

    # Basic JSON config
    app.config["JSON_SORT_KEYS"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

    # Enable CORS so Angular can connect
    CORS(app)

    # Register route blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(flights_bp)
    app.register_blueprint(trees_bp)
    app.register_blueprint(queue_bp)
    app.register_blueprint(versions_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(undo_bp)
    app.register_blueprint(business_bp)

    return app


app = create_app()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║                SkyBalance Backend API                   ║
║                                                          ║
║  URL base:  http://localhost:5000                       ║
║  Health:    http://localhost:5000/api/health            ║
║                                                          ║
║  Backend listo para conectar con Angular                ║
╚══════════════════════════════════════════════════════════╝
""")

    app.run(debug=True, host="0.0.0.0", port=5000)