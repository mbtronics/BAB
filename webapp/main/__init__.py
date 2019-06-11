from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, userviews, resourceviews, skillviews, reservationviews, availableviews, paymentviews, settingsviews
from . import errors
from ..usermodels import Permission


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
