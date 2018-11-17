import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from config import config_dict
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from redis import StrictRedis
from config import Config

redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)



db = SQLAlchemy()


#设置日志的记录的等级
logging.basicConfig(level=logging.DEBUG)
#创建日志记录器，指明日志保存的路径，每个日志文件的大小，保存的日志文件个数上限
file_log_handler = RotatingFileHandler('logs/log',maxBytes=1024*1024*100, backupCount=10)
#创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
#为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
#为全局的日志工具对象（flask app使用的） 添加日志记录器
logging.getLogger().addHandler(file_log_handler)


#项目开启csrf保护
from flask_wtf import CSRFProtect,csrf


def creat_app(config_name):

    app = Flask(__name__)
    app.config.from_object(config_dict[config_name])

    db.init_app(app)
    Session(app)
    #开启CSRF保护
    CSRFProtect(app)

    #生成csrf_token 给每个客户端都设置csrf_token
    @app.after_request
    def after_request(response):
       csrf_token =  csrf.generate_csrf()
       response.set_cookie('csrf_token', csrf_token)
       return response

    from info.modules.news import news_blue
    app.register_blueprint(news_blue)
    from info.modules.passport import passport_blue
    app.register_blueprint(passport_blue)
    return app


