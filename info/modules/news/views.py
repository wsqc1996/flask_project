from flask import current_app

from . import news_blue
from flask import session,render_template


@news_blue.route('/')
def index():
    # session['name'] = 'qicheng'
    return render_template('news/index.html')


@news_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')