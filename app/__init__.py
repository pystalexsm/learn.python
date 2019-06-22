import locale
import logging
from datetime import datetime

from flask import Flask, redirect, render_template, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy import exc

from app.album import album as album_blueprint
from app.auth_ import auth_ as auth_blueprint
from app.auth_.models import User
from app.blockchain import blockchain as blockchain_blueprint
from app.database import db
from app.email import mail
from app.event import event as event_blueprint
from app.event.models import Event, EventFiles
from app.files import files as files_blueprint
from app.files.models import Files
from app.profile import profile as profile_blueprint
from config import Config

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

login = LoginManager()
migrate = Migrate()

logging.basicConfig(filename='error.log', format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)


def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    Config.init_app(app)

    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    login.init_app(app)

    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Event=Event, Files=Files, EventFiles=EventFiles)

    @app.context_processor
    def init():
        return {
            'now': datetime.now()
        }

    @app.template_filter('formatdatetime')
    def format_datetime(value, format="%d %B, %Y %H:%M"):
        """Format a date time to (Default): %d %B, %Y %H:%M"""
        if value is None:
            return ""
        return value.strftime(format)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('/404.html', title=404), 404

    @login.user_loader
    def load_user(user_id):
        """
        проверка авторизации
        :param user_id: идентификатор пользователя
        :return: user | None
        """

        try:
            user_ = User.query.filter_by(id=int(user_id)).first()
            if user_ is not None:
                return user_
        except (exc.OperationalError, TypeError) as ex:
            # логирование
            logging.exception(ex)
            return None

        return None

    @login.unauthorized_handler
    def unauthorized_callback():
        return redirect(url_for('auth_.login'))

    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(profile_blueprint, url_prefix='/')
    app.register_blueprint(event_blueprint, url_prefix='/events')
    app.register_blueprint(files_blueprint, url_prefix='/files')
    app.register_blueprint(album_blueprint, url_prefix='/album')
    app.register_blueprint(blockchain_blueprint, url_prefix='/blockchain')

    return app
