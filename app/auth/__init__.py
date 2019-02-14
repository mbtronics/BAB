from flask import Blueprint, session

auth = Blueprint('auth', __name__)

from . import views


@auth.before_app_request
def before_request():

    try:
        foo = session.items()
    except TypeError:
        # fixes for python 2 => 3 upgrade
        session.clear()
