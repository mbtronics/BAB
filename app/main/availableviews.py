from flask import render_template, request, Response, abort, jsonify
from flask.ext.login import login_required, current_user
from . import main
from .. import db
from ..usermodels import Permission
from ..resourcemodels import Resource, Available, Reservation
from ..decorators import permission_required
import json
from sqlalchemy import and_
from datetime import datetime, timedelta


@main.route('/resource/available/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RESOURCES)
def available(id):
    resource = Resource.query.get_or_404(id)
    return render_template('resource/available.html', resource=resource)


@main.route('/resource/available/<int:id>/getdata', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RESOURCES)
def available_getdata(id):
    resource = Resource.query.get_or_404(id)

    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')

    if start_date and end_date:
        data = []
        for a in resource.availability.filter(and_(Available.start>=start_date, Available.end<=end_date)):
            data.append( {
                'start': a.start.strftime("%Y-%m-%d %H:%M:%S"),
                'end': a.end.strftime("%Y-%m-%d %H:%M:%S"),
                'id': a.id,
                'title': a.user.name,
            })

        for r in resource.reservations.filter(and_(Reservation.start>=start_date, Reservation.end<=end_date)):
            data.append( {
                'start': r.start.strftime("%Y-%m-%d %H:%M:%S"),
                'end': r.end.strftime("%Y-%m-%d %H:%M:%S"),
                'id': 'reservation',
                'title': r.user.name,
                'rendering': 'background',
                'color': '#6aa4c1'
            })

        return Response(json.dumps(data), mimetype='application/json')

    abort(404)


@main.route('/resource/available/<int:id>/setdata', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RESOURCES)
def available_setdata(id):
    resource = Resource.query.get_or_404(id)
    data = request.get_json()

    if data and 'action' in data:

        if data['action']=='new':
            start = datetime.fromtimestamp(data['start']) + timedelta(minutes=data['offset'])
            end = datetime.fromtimestamp(data['end']) + timedelta(minutes=data['offset'])

            if start < datetime.now() or end < datetime.now():
                return jsonify({'err': "You can't make this resource available in the past!"})

            a=Available(start=start, end=end, resource=resource, user=current_user)
            db.session.add(a)
            db.session.commit()
            return jsonify({'id': a.id})

        elif data['action']=='update':
            a=Available.query.get_or_404(data['id'])

            start = datetime.fromtimestamp(data['start']) + timedelta(minutes=data['offset'])
            end = datetime.fromtimestamp(data['end']) + timedelta(minutes=data['offset'])

            if (start!=a.start and start < datetime.now()) or (end!=a.end and end < datetime.now()):
                return jsonify({'err': "You can't update availability in the past!"})

            reservations = resource.reservations.filter(and_(Reservation.start>=a.start, Reservation.end<=a.end)).all()
            for reservation in reservations:
                if reservation.start<start or reservation.end>end:
                    return jsonify({'err': "Existing reservation within new availability range"})

            a.start = start
            a.end = end
            db.session.add(a)
            return jsonify()

        elif data['action']=='remove':
            a=Available.query.get_or_404(data['id'])

            if a.start < datetime.now() or a.end < datetime.now():
                return jsonify({'err': "You can't update availability in the past!"})

            reservations = resource.reservations.filter(and_(Reservation.start>=a.start, Reservation.end<=a.end)).all()
            if len(reservations)>0:
                return jsonify({'err': 'There are reservations in this availability range'})

            db.session.delete(a)

    abort(404)
