from flask import Blueprint
bas = Blueprint('bas', __name__)


from .bas_api import BASApi

bas_view = BASApi.as_view('bas_view')
bas.add_url_rule('/auth', view_func=bas_view, methods=['POST'])
