from functools import wraps
from flask import abort
from flask.ext.login import current_user
from .usermodels import Permission


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)

def moderator_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_moderator():
            abort(403)
        return func(*args, **kwargs)
    return decorated_view

def authorise_download(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):

        if 'setname' in kwargs and kwargs['setname']=='expensenotes':
            if not current_user.is_authenticated:
                abort(403)
            if not current_user.is_moderator():
                abort(403)

        return func(*args, **kwargs)
    return decorated_view