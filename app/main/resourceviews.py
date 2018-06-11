from flask import render_template, redirect, url_for, request, abort
from flask.ext.login import login_required, current_user
from . import main
from .forms import DeleteConfirmationForm, EditResourceForm
from .. import db
from ..usermodels import Permission, Skill
from ..resourcemodels import Resource
from ..decorators import permission_required
from .. import photos

@main.route('/resource/<name>')
def resource(name):
    resource = Resource.query.filter_by(name=name).first_or_404()

    if not resource.active and not current_user.can(Permission.MANAGE_RESOURCES):
        abort(403)

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
        resource.skill_required = form.skill_required.data
        resource.price_p_per = form.price_p_per.data
        resource.reserv_per = form.reserv_per.data

        if form.photo.data.filename:
            resource.photo_filename = photos.save(form.photo.data)

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
        resource.skill_required = form.skill_required.data
        resource.price_p_per = form.price_p_per.data
        resource.reserv_per = form.reserv_per.data

        if form.photo.data.filename:
            resource.photo_filename = photos.save(form.photo.data)

        db.session.add(resource)
        return redirect(url_for('.resource', name=resource.name))

    form.name.data = resource.name
    form.description.data = resource.description
    form.active.data = resource.active
    form.skill_required = resource.skill_required
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

