from . import news_blue
from flask import session


@news_blue.route('/')
def index():
    session['name'] = 'qicheng'
    return 'hello 2019'