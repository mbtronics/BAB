from flask import Blueprint

main = Blueprint('main', __name__)

from . import availableviews, paymentviews, reservationviews, resourceviews, settingsviews, skillviews, userviews, views


@main.app_context_processor
def inject_permissions():
    from models.usermodels import Permission
    return dict(Permission=Permission)
