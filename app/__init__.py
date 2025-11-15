import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize the database extension
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import and register blueprints here if you have them
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

from app import models
