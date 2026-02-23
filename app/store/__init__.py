from flask import Blueprint

bp = Blueprint("store", __name__)

from app.store import routes  # noqa: F401
