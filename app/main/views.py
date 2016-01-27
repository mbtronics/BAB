from flask import abort, request, current_app, render_template, g
from flask.ext.sqlalchemy import get_debug_queries
from . import main
from ..resourcemodels import Resource
import sys, os, signal

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.before_app_request
def before_request():
    g.resources = Resource.query.filter_by(active=True).all()


@main.route('/shutdown')
def server_shutdown():
    pid = os.getpid()
    os.kill(pid, signal.SIGHUP)

    sys.exit()
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')
