from flask import flash, redirect, render_template, url_for
from flask_login import login_required

from . import main
from .. import db
from ..decorators import permission_required
from ..resourcemodels import Resource
from ..usermodels import Permission, Skill
from .forms import DeleteConfirmationForm, EditSkillForm


@main.route('/skill/<name>')
@login_required
def skill(name):
    skill = Skill.query.filter_by(name=name).first_or_404()
    resources = skill.resources.order_by(Resource.name.asc()).all()
    return render_template('skill/view.html', skill=skill, resources=resources)


@main.route('/skill/add', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SKILLS)
def add_skill():
    form = EditSkillForm()
    if form.validate_on_submit():
        skill = Skill()
        skill.name = form.name.data
        skill.description = form.description.data
        db.session.add(skill)
        return redirect(url_for('.skill', name=skill.name))

    return render_template('skill/edit.html', form=form)


@main.route('/skill/<name>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SKILLS)
def edit_skill(name):
    skill = Skill.query.filter_by(name=name).first_or_404()

    form = EditSkillForm()
    if form.validate_on_submit():
        skill.name = form.name.data
        skill.description = form.description.data
        db.session.add(skill)
        return redirect(url_for('.skill', name=skill.name))

    form.name.data = skill.name
    form.description.data = skill.description
    return render_template('skill/edit.html', form=form)


@main.route('/skill/<name>/delete', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SKILLS)
def delete_skill(name):
    skill = Skill.query.filter_by(name=name).first_or_404()

    form = DeleteConfirmationForm()
    if form.validate_on_submit() and form.delete.data:

        if skill.num_users>0:
            flash("You can't delete a skill wich has users!")
            return redirect(url_for('.skill', name=skill.name))

        if len(skill.resources.all())>0:
            flash("You can't delete a skill wich has resources attached!")
            return redirect(url_for('.skill', name=skill.name))

        db.session.delete(skill)
        db.session.commit()
        return redirect(url_for('.list_skills'))

    return render_template('delete_confirmation.html', name=skill.name, form=form)


@main.route('/skills')
@login_required
def list_skills():
    skills = Skill.query.order_by(Skill.name.asc()).all()
    return render_template('skill/list.html', skills=skills)
