from flask import session
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand
from info import creat_app,db

app = creat_app('development')

Migrate(app, db)
manage = Manager(app)
manage.add_command('db', MigrateCommand)


@app.route('/')
def index():
    session['name'] = 'qicheng'
    return 'hello 2019'

if __name__ == '__main__':
    # app.run(debug=True)
    manage.run()