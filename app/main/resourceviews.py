from flask import render_template, redirect, url_for, request, Response, abort, jsonify
from flask.ext.login import login_required, current_user
from . import main
from .forms import DeleteConfirmationForm, EditResourceForm
from .. import db
from ..usermodels import Permission, Skill
from ..resourcemodels import Resource, Available, Reservation
from ..decorators import permission_required
import json
from sqlalchemy import and_
from datetime import datetime, timedelta

@main.route('/resource/<name>')
@login_required
def resource(name):
    resource = Resource.query.filter_by(name=name).first_or_404()
    skills = resource.skills.order_by(Skill.name.asc()).all()
    return render_template('resource/view.html', resource=resource, skills=skills)


@main.route('/resource/add', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RESOURCES)
def add_resource():
    form = EditResourceForm()
    if form.validate_on_submit():
        resource = Resource()
        resource.name = form.name.data
        resource.description = form.description.data
        resource.active = form.active.data
        resource.image_url = form.image_url.data
        resource.price_p_per = form.price_p_per.data
        resource.reserv_per = form.reserv_per.data
        db.session.add(resource)
        return redirect(url_for('.resource', name=resource.name))

    return render_template('resource/edit.html', form=form)


@main.route('/resource/<name>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RESOURCES)
def edit_resource(name):
    resource = Resource.query.filter_by(name=name).first_or_404()

    form = EditResourceForm()
    if form.validate_on_submit():
        resource.name = form.name.data
        resource.description = form.description.data
        resource.active = form.active.data
        resource.image_url = form.image_url.data
        resource.price_p_per = form.price_p_per.data
        resource.reserv_per = form.reserv_per.data
        db.session.add(resource)
        return redirect(url_for('.resource', name=resource.name))

    form.name.data = resource.name
    form.description.data = resource.description
    form.active.data = resource.active
    form.image_url.data = resource.image_url
    form.price_p_per.data = resource.price_p_per
    form.reserv_per.data = resource.reserv_per
    return render_template('resource/edit.html', form=form)


@main.route('/resource/<name>/delete', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SKILLS)
def delete_resource(name):
    resource = Resource.query.filter_by(name=name).first_or_404()

    form = DeleteConfirmationForm()
    if form.validate_on_submit() and form.delete.data:
        db.session.delete(resource)
        db.session.commit()
        return redirect(url_for('.list_resources'))

    return render_template('delete_confirmation.html', name=resource.name, form=form)


@main.route('/resources')
@login_required
def list_resources():
    resources = Resource.query.order_by(Resource.name.asc()).all()
    return render_template('resource/list.html', resources=resources)

@main.route('/resource/<int:id>/edit-skills', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RESOURCES)
def edit_resource_skills(id):
    resource = Resource.query.get_or_404(id)

    skills = Skill.query.order_by(Skill.name.asc()).all()

    if request.method == 'POST':
        for skill in skills:
            if skill.name in request.form.keys():
                if not skill in resource.skills.all():
                    resource.skills.append(skill)
            else:
                if skill in resource.skills.all():
                    resource.skills.remove(skill)

        db.session.commit()
        return redirect(url_for('.resource', name=resource.name))
    else:
        resource_skills = [ skill.name for skill in resource.skills.all() ]
        return render_template('resource/edit_skills.html', resource=resource, skills=skills, resource_skills=resource_skills)


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

        return Response(json.dumps(data), mimetype='application/json')

    abort(404)

@main.route('/resource/available/<int:id>/setdata', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_RESOURCES)
def available_setdata(id):
    resource = Resource.query.get_or_404(id)
    data = request.get_json()

    if data and 'action' in data:

        if data['action']=='update' or data['action']=='remove':
            a=Available.query.get_or_404(data['id'])
        elif data['action']=='new':
            a=Available()
        else:
            abort(404)

        if data['action']=='remove':
            db.session.delete(a)
        else:
            start = datetime.fromtimestamp(data['start']) + timedelta(minutes=data['offset'])
            end = datetime.fromtimestamp(data['end']) + timedelta(minutes=data['offset'])
            #TODO: check for overlap
            #TODO: don't move if somebody made a reservation
            a.start = start
            a.end = end
            a.resource = resource
            a.user = current_user
            db.session.add(a)

        db.session.commit()
        return jsonify({'id': a.id})

    abort(404)  #TODO: fix json error returns

@main.route('/resource/reservation/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK)
def reservation(id):
    resource = Resource.query.get_or_404(id)
    return render_template('resource/reservation.html', resource=resource)

@main.route('/resource/reservation/<int:id>/getdata', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK)
def reservation_getdata(id):
    resource = Resource.query.get_or_404(id)

    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')

    if start_date and end_date:
        data = []
        for r in resource.reservations.filter(and_(Reservation.start>=start_date, Reservation.end<=end_date)):

            if r.user.id==current_user.id or current_user.can(Permission.MANAGE_RESOURCES):
                if r.user.name:
                    title=r.user.name
                else:
                    title=r.user.username
            else:
                title='Reserved'

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

        for r in resource.availability.filter(and_(Available.start>=start_date, Available.end<=end_date)):
            data.append( {
                'start': r.start.strftime("%Y-%m-%d %H:%M:%S"),
                'end': r.end.strftime("%Y-%m-%d %H:%M:%S"),
                'id': 'available',
                'rendering': 'background',
            })

        return Response(json.dumps(data), mimetype='application/json')

    abort(404)#TODO: fix json error returns

@main.route('/resource/reservation/<int:id>/setdata', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.BOOK)
def reservation_setdata(id):
    resource = Resource.query.get_or_404(id)

    data = request.get_json()

    if data and 'action' in data:

        if data['action']=='update' or data['action']=='remove':
            r=Reservation.query.get_or_404(data['id'])

            if r.user!=current_user and not current_user.can(Permission.MANAGE_RESOURCES):
                return jsonify()

        elif data['action']=='new':
            r=Reservation()
        else:
            abort(404)#TODO: fix json error returns

        if data['action']=='remove':
            db.session.delete(r)
        else:
            start = datetime.fromtimestamp(data['start']) + timedelta(minutes=data['offset'])
            end = datetime.fromtimestamp(data['end']) + timedelta(minutes=data['offset'])

            #TODO: check if these dates are in a valid (available) range and do not overlap
            r.start = start
            r.end = end
            r.resource = resource

            if not r.user:
                r.user = current_user

            db.session.add(r)

        db.session.commit()
        return jsonify({'id': r.id})

    abort(404)#TODO: fix json error returns