from config import config
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_pagedown import PageDown
from flask_qrcode import QRcode
from flask_sqlalchemy import SQLAlchemy
from flask_thumbnails import Thumbnail
from flask_uploads import EXECUTABLES, IMAGES, AllExcept, UploadSet, configure_uploads
from flask_wtf import CSRFProtect
from mollie.api.client import Client


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
qrcode = QRcode()
pagedown = PageDown()
photos = UploadSet('photos', IMAGES)
expensenotes = UploadSet('expensenotes', AllExcept(EXECUTABLES))
thumb = Thumbnail()
mollie = Client()
csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name, url_prefix):

    if url_prefix == "" or url_prefix == "/":
        main_prefix=None
        auth_prefix='/auth'
        static_prefix='/static'
        media_url='_uploads/photos/'
    else:
        if url_prefix.endswith('/'):
            url_prefix=url_prefix[:-1]
        main_prefix=url_prefix
        auth_prefix=url_prefix+'/auth'
        static_prefix='%s/static' % url_prefix
        media_url='%s/_uploads/photos/' % url_prefix[1:]

        from flask_uploads import uploads_mod
        uploads_mod.url_prefix = '%s/_uploads' % url_prefix

    app = Flask(__name__, static_url_path=static_prefix)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    qrcode.init_app(app)
    pagedown.init_app(app)
    configure_uploads(app, (photos, expensenotes))

    app.config['MEDIA_FOLDER'] = app.config['UPLOADED_PHOTOS_DEST']
    app.config['MEDIA_URL'] = media_url

    thumb.init_app(app)
    mollie.set_api_key(app.config['MOLLIE_KEY'])
    csrf.init_app(app)

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix=main_prefix)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix=auth_prefix)

    from .decorators import authorise_download
    app.view_functions['_uploads.uploaded_file'] = authorise_download(app.view_functions['_uploads.uploaded_file'])

    return app
