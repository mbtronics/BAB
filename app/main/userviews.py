from flask import render_template, redirect, url_for, abort, flash, request, session
from flask.ext.login import login_required, current_user
from sqlalchemy import or_
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, DeleteConfirmationForm, SearchUserForm
from .. import db
from ..usermodels import Permission, Role, User, Skill
from ..decorators import permission_required

NumPaginationItems = 20

@main.route('/user/<username>')
def user(username):
    print username
    print User.query.filter_by(username=username).first()
    user = User.query.filter_by(username=username).first_or_404()
    skills = user.skills.order_by(Skill.name.asc()).all()
    return render_template('user/view.html', user=user, skills=skills)


@main.route('/user/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('user/edit.html', form=form)


@main.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def edit_profile_admin(id):
    user = User.query.get_or_404(id)

    if user.is_administrator() and not current_user.is_administrator():
        flash('Only the administrator can access this!', 'error')
        abort(404)

    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me

    return render_template('user/edit.html', form=form, user=user)

@main.route('/user/<int:id>/edit-skills', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def edit_skills(id):
    user = User.query.get_or_404(id)

    if user.is_administrator() and not current_user.is_administrator():
        flash('Only the administrator can access this!', 'error')
        abort(404)

    skills = Skill.query.order_by(Skill.name.asc()).all()

    if request.method == 'POST':
        for skill in skills:
            if skill.name in request.form.keys():
                if not skill in user.skills.all():
                    user.skills.append(skill)
            else:
                if skill in user.skills.all():
                    user.skills.remove(skill)

        db.session.commit()
        return redirect(url_for('.user', username=user.username))
    else:
        user_skills = [ skill.name for skill in user.skills.all() ]
        return render_template('user/edit_skills.html', user=user, skills=skills, user_skills=user_skills)

@main.route('/users')
@login_required
@permission_required(Permission.MANAGE_USERS)
def list_users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.member_since.desc()).paginate(page, per_page=NumPaginationItems, error_out=False)
    users = pagination.items
    return render_template('user/list.html', users=users, pagination=pagination)

@main.route('/user/<int:id>/delete', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def delete_user(id):
    user = User.query.get_or_404(id)

    if user.is_administrator():
        flash("Can not delete administrator!", 'error')
        abort(404)

    form = DeleteConfirmationForm()
    if form.validate_on_submit() and form.delete.data:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('.list_users'))

    return render_template('delete_confirmation.html', name=user.username, form=form)

@main.route('/users/search', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def search_users():
    form = SearchUserForm()
    page = request.args.get('page', type=int)

    if form.validate_on_submit():
        if form.id.data:
            user = User.query.get_or_404(form.id.data)
            return redirect(url_for('.user', username=user.username))
        elif form.name.data:
            session['name'] = form.name.data
            page = 1

    if page is not None and session['name'] is not None:
        q = User.query.filter(or_(User.name.like('%'+session['name']+'%'), User.username.like('%'+session['name']+'%')))
        pagination = q.order_by(User.username.asc()).paginate(page, NumPaginationItems, error_out=False)
        users = pagination.items

        if len(users)==0:
            flash('No users found')
        else:
            flash('%d users found, showing %d' % (pagination.total, len(pagination.items)))

        form = SearchUserForm(name=session['name'])

        return render_template('user/search.html', form=form, users=users, pagination=pagination)

    return render_template('user/search.html', form=form)
