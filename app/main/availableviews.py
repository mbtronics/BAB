import json
from datetime import datetime

import dateutil.parser
from flask import Response, abort, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_

from . import main
from .. import db
from ..decorators import permission_required
from models.resourcemodels import Available, Reservation
from models.usermodels import Permission


@main.route('/available', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RESOURCES)
def available():
    return render_template('resource/available.html')


@main.route('/user-by-available/<int:id>', methods=['GET', 'POST'])
def user_by_available(id):
    a = Available.query.get_or_404(id)
    return redirect(url_for('.user', username=a.user.username))


@main.route('/available/getdata', methods=['GET', 'POST'])
def available_getdata():

    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')

    if start_date and end_date:
        data = []
        for a in Available.query.filter(and_(Available.start>=start_date, Available.end<=end_date)):
            data.append( {
                'start': a.start.strftime("%Y-%m-%d %H:%M:%S"),
                'end': a.end.strftime("%Y-%m-%d %H:%M:%S"),
                'id': a.id,
                'title': a.user.name,
            })

        for r in Reservation.query.filter(and_(Reservation.start>=start_date, Reservation.end<=end_date)):
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


def check_previous_timeblock(start):
    availables = Reservation.query.filter(Available.end==start).filter(Available.user==current_user).all()
    return len(availables)>0


def check_next_timeblock(end):
    availables = Reservation.query.filter(Available.start==end).filter(Available.user==current_user).all()
    return len(availables) > 0


@main.route('/available/setdata', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RESOURCES)
def available_setdata():
    data = request.get_json()

    if data and 'action' in data:

        if data['action']=='new':
            start = dateutil.parser.parse(data['start'], ignoretz=True)
            end = dateutil.parser.parse(data['end'], ignoretz=True)

            if start < datetime.now() or end < datetime.now():
                return jsonify({'err': "You can't make this resource available in the past!"})

            if check_previous_timeblock(start):
                return jsonify({'err': 'You should extend the previous period, not create a new one. You can drag the bottom of a period down to extend it.'})

            if check_next_timeblock(end):
                return jsonify({'err': 'You should move the next period up and extend it, not create a new one. You can drag the bottom of the a period down to extend it.'})

            a=Available(start=start, end=end, user=current_user)
            db.session.add(a)
            db.session.commit()
            return jsonify({'id': a.id})

        elif data['action']=='update':
            a=Available.query.get_or_404(data['id'])

            start = dateutil.parser.parse(data['start'], ignoretz=True)
            end = dateutil.parser.parse(data['end'], ignoretz=True)

            if (start!=a.start and start < datetime.now()) or (end!=a.end and end < datetime.now()):
                return jsonify({'err': "You can't update availability in the past!"})

            reservations = Reservation.query.filter(and_(Reservation.start>=a.start, Reservation.end<=a.end)).all()
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

            reservations = Reservation.query.filter(and_(Reservation.start>=a.start, Reservation.end<=a.end)).all()
            if len(reservations)>0:
                for reservation in reservations:
                    if not reservation.user.is_moderator:
                        availabilities = Available.query.filter(and_(Available.start <= reservation.start, Available.end >= reservation.end)).all()
                        if len(availabilities)==1:
                            return jsonify({'err': 'There are reservations in this availability range'})

            db.session.delete(a)

    abort(404)
