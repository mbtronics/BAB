from flask import render_template, abort, request, current_app
from flask.ext.sqlalchemy import get_debug_queries
from . import main
from flask.ext.login import login_required
from ..decorators import permission_required
from ..usermodels import Permission
from ..resourcemodels import Resource

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
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

@main.route('/reservation/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK)
def reservations(id):
    resource = Resource.query.get_or_404(id)
    return render_template('reservation.html', resource=resource)