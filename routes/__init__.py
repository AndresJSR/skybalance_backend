"""Shared objects and helpers for API routes."""

from flask import jsonify
from services.tree_service import TreeService

# Single shared service instance for the whole API
service = TreeService()


def success_response(data, status_code=200):
    """
    Standard JSON success response.
    """
    return jsonify(data), status_code


def error_response(message, status_code=400):
    """
    Standard JSON error response.
    """
    return jsonify({"error": message}), status_code