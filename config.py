from redis import StrictRedis


class Config:
    DEBUG = None

    SECRET_KEY = '8v3c8SCjBJLIF1zEqW7DfxPRK5gF9iZeaBhia8qVxqpr88KOoCzUJrbpSLg1'

    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@loclhost/flask_project2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host='127.0.0.1', port=6379)
    SESSION_USE_SIGNER = True

    PERMANENT_SESSION_LIFETIME = 86400



class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_dict ={
    'development':DevelopmentConfig,
    'production':ProductionConfig
}