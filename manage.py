from flask import Flask,session
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from config import config_dict

app = Flask(__name__)
app.config.from_object(config_dict['development'])

db = SQLAlchemy(app)
Migrate(app, db)
Session(app)

manage = Manager(app)
manage.add_command('db', MigrateCommand)


@app.route('/')
def index():
    session['name'] = 'qicheng'
    return 'hello 2019'

if __name__ == '__main__':
    # app.run(debug=True)
    manage.run()