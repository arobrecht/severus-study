from flask import Blueprint

from ..manager import Manager
main = Blueprint('main', __name__, template_folder="templates", static_folder="../static", static_url_path="/static")
# main.app = None # Will be set by the factory

from . import routes, events, snape_events
