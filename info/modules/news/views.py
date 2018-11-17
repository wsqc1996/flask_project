from flask import current_app,session
from info.models import User
from . import news_blue
from flask import session,render_template


@news_blue.route('/')
def index():
    user_id = session.get('user_id')
    user = None
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
    data = {
        'user_info':user.to_dict() if user else None
    }
    return render_template('news/index.html',data=data)


@news_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')