from flask import render_template, redirect, url_for, abort, flash
from flask.ext.login import login_required
from . import main
from .forms import DeleteConfirmationForm, EditSkillForm
from .. import db
from ..usermodels import Permission, Skill
from ..decorators import permission_required

@main.route('/skill/<name>')
@login_required
def skill(name):
    skill = Skill.query.filter_by(name=name).first_or_404()
    return render_template('skill/view.html', skill=skill)


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


@main.route('/skill/edit', methods=['GET', 'POST'])
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
        db.session.delete(skill)
        db.session.commit()
        return redirect(url_for('.list_skills'))

    return render_template('delete_confirmation.html', name=skill.name, form=form)


@main.route('/skills')
@login_required
def list_skills():
    skills = Skill.query.order_by(Skill.name.asc()).all()
    return render_template('skill/list.html', skills=skills)
