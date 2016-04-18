from flask import render_template, request, Response, abort, jsonify
from flask.ext.login import login_required, current_user
from . import main
from .. import db
from ..usermodels import Permission
from ..resourcemodels import Resource, Available, Reservation
from ..decorators import permission_required
import json
from sqlalchemy import and_, or_
from datetime import datetime
import dateutil.parser

@main.route('/resource/reservation/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK)
def make_reservation(id):
    resource = Resource.query.get_or_404(id)

    if not resource.active and not current_user.can(Permission.MANAGE_RESOURCES):
        abort(403)

    return render_template('resource/make_reservation.html', resource=resource)

def get_data_json_response(resources, start_date, end_date):
    if start_date and end_date:
        data = []
        for resource in resources:
            for r in resource.reservations.filter(and_(Reservation.start>=start_date, Reservation.end<=end_date)):
                if r.user.id==current_user.id or current_user.can(Permission.MANAGE_RESOURCES):
                    title = r.user.name
                    if len(resources)>1:
                        title += '\n' + resource.name
                    else:
                        title += '\n' + r.reason
                else:
                    title='Reserved'    #'Reserved' used in _calendar.html

                if r.user.id==current_user.id:
                    color='#378006'
                else:
                    color=''

                data.append( {
                    'start': r.start.strftime("%Y-%m-%d %H:%M:%S"),
                    'end': r.end.strftime("%Y-%m-%d %H:%M:%S"),
                    'id': r.id,
                    'title': title,
                    'constraint': 'available',
                    'color': color,
                })

            for r in Available.query.filter(and_(Available.start>=start_date, Available.end<=end_date)):
                data.append( {
                    'start': r.start.strftime("%Y-%m-%d %H:%M:%S"),
                    'end': r.end.strftime("%Y-%m-%d %H:%M:%S"),
                    'id': 'available',
                    'rendering': 'background',
                })
        return Response(json.dumps(data), mimetype='application/json')

    abort(404)#TODO: fix json error returns

@main.route('/resource/reservation/getdata', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK)
def reservation_getdata_all():
    resources = Resource.query.filter_by(active=True).all()
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    return get_data_json_response(resources, start_date, end_date)


@main.route('/resource/reservation/<int:id>/getdata', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK)
def reservation_getdata(id):
    resources = [Resource.query.get_or_404(id)]
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    return get_data_json_response(resources, start_date, end_date)


@main.route('/resource/reservation/<int:id>/setdata', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK)
def reservation_setdata(id):
    resource = Resource.query.get_or_404(id)
    data = request.get_json()

    if data and 'action' in data:
        if data['action']=='new':
            start = dateutil.parser.parse(data['start'], ignoretz=True)
            end = dateutil.parser.parse(data['end'], ignoretz=True)

            if start < datetime.now() or end < datetime.now():
                return jsonify({'err': "You can't make reservations in the past!"})

            #Check for overlap
            reservations = Reservation.query.filter(Reservation.resource==resource).filter(or_(\
                                                        and_(Reservation.start<=start, Reservation.end>=end), \
                                                        and_(Reservation.start>=start, Reservation.start<end), \
                                                        and_(Reservation.end>start, Reservation.end<=end))).all()
            if len(reservations)>0:
                return jsonify({'err': "Overlap with existing reservation"})

            r=Reservation(start=start, end=end, resource=resource, user=current_user, reason=data['reason'])
            r.cost = r.calculated_cost
            db.session.add(r)
            db.session.commit()
            return jsonify({'id': r.id})

        elif data['action']=='update':
            r=Reservation.query.get_or_404(data['id'])

            if r.user!=current_user and not current_user.can(Permission.MANAGE_RESERVATIONS):
                return jsonify({'err': "Permission denied"})

            start = dateutil.parser.parse(data['start'], ignoretz=True)
            end = dateutil.parser.parse(data['end'], ignoretz=True)

            if (start!=r.start and start < datetime.now()) or (end!=r.end and end < datetime.now()):
                return jsonify({'err': "You can't update reservations in the past!"})

            #Check for overlap
            reservations = Reservation.query.filter(Reservation.resource==resource).filter(or_(\
                                                        and_(Reservation.start<=start, Reservation.end>=end), \
                                                        and_(Reservation.start>=start, Reservation.start<end), \
                                                        and_(Reservation.end>start, Reservation.end<=end)))\
                                            .filter(Reservation.id!=r.id).all()
            if len(reservations)>0:
                return jsonify({'err': "Overlap with existing reservation"})

            r.start = start
            r.end = end
            r.cost = r.calculated_cost
            db.session.add(r)
            return jsonify()

        elif data['action']=='remove':
            r=Reservation.query.get_or_404(data['id'])

            if r.user!=current_user and not current_user.can(Permission.MANAGE_RESERVATIONS):
                return jsonify({'err': "Permission denied"})

            if r.start < datetime.now() or r.end < datetime.now():
                return jsonify({'err': "You can't delete reservations in the past!"})

            db.session.delete(r)
            return jsonify()

    abort(404)


@main.route('/reservation/<int:id>', methods=['GET', 'POST'])
@login_required
def reservation(id):
    reservation = Reservation.query.get_or_404(id)

    if reservation.user!=current_user and not current_user.can(Permission.MANAGE_RESERVATIONS):
        abort(404)

    return render_template('resource/reservation.html', reservation=reservation)


@main.route('/reservation/overview')
@login_required
@permission_required(Permission.MANAGE_RESERVATIONS)
def reservation_overview():
    return render_template('resource/reservation_overview.html')
