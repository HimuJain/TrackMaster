import os

# this flask backend is just a REST API for the frontend to consume.

from flask import Flask
from flask_cors import CORS
from . import settings

from .routes import bp


# from .extensions import db

project_dir = os.path.dirname(os.path.abspath(__file__))

def create_app(config_object=settings):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    CORS(app, resources={r"/*": {"origins": "*"}})

    app.register_blueprint(bp)
    register_errorhandlers(app) # ==> error handlers return JSON.


    return app


def register_errorhandlers(app):
    """Register error handlers."""
    @app.errorhandler(401)
    def forbidden_error(error):
        return {"status":"401","message":"forbidden"}

    @app.errorhandler(404)
    def page_not_found(error):
        return {"status":"404","message":"not found"}

    @app.errorhandler(500)
    def internal_error(error):
        return {"status":"500","message":"internal server error"}

    return None
