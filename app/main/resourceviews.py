from flask import render_template, redirect, url_for, abort, flash
from flask.ext.login import login_required
from . import main
from .forms import DeleteConfirmationForm, EditResourceForm
from .. import db
from ..usermodels import Permission
from ..resourcemodels import Resource
from ..decorators import permission_required

@main.route('/resource/<name>')
@login_required
def resource(name):
    resource = Resource.query.filter_by(name=name).first_or_404()
    return render_template('resource/view.html', resource=resource)


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