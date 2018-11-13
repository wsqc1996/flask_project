from flask import Flask
from config import config_dict
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

db = SQLAlchemy()
def creat_app(config_name):

    app = Flask(__name__)
    app.config.from_object(config_dict[config_name])
    db.init_app(app)
    Session(app)
    return app


