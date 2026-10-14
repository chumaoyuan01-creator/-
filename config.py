"""应用配置模块"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:////var/lib/flask-app/articles.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'articles.db'
    )


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


def get_config():
    """根据环境变量获取对应配置"""
    env = os.environ.get('FLASK_ENV', 'production')
    configs = {
        'production': ProductionConfig,
        'development': DevelopmentConfig,
        'testing': TestingConfig,
    }
    return configs.get(env, ProductionConfig)


def setup_logging(app):
    """配置应用日志"""
    log_dir = '/var/log/flask-app'
    os.makedirs(log_dir, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    ))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask app started')
