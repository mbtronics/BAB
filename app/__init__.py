from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.qrcode import QRcode
from flask.ext.pagedown import PageDown
from flask.ext.uploads import configure_uploads, UploadSet, IMAGES
from flask.ext.thumbnails import Thumbnail
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
qrcode = QRcode()
pagedown = PageDown()
photos = UploadSet('photos', IMAGES)
thumb = Thumbnail()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name, url_prefix):
    app = Flask(__name__, static_url_path='%sstatic'%url_prefix)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    qrcode.init_app(app)
    pagedown.init_app(app)
    configure_uploads(app, (photos))

    app.config['MEDIA_FOLDER'] = app.config['UPLOADED_PHOTOS_DEST']
    app.config['MEDIA_URL'] = '_uploads/photos/'    #TODO: make this configurable

    thumb.init_app(app)

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)


    if url_prefix == "" or url_prefix == "/":
        main_prefix=None
        auth_prefix='/auth'
    else:
        if url_prefix.endswith('/'):
            url_prefix=url_prefix[:-1]

        main_prefix=url_prefix
        auth_prefix=url_prefix+'/auth'

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix=main_prefix)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix=auth_prefix)

    return app
