from flask import render_template, redirect, url_for, abort, flash, request, current_app, session
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
from sqlalchemy import or_
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, DeleteUserForm, SearchUserForm, EditSkillForm
from .. import db
from ..usermodels import Permission, Role, User, Skill
from ..decorators import permission_required

NumPaginationItems = 20

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


@main.route('/user/<username>')
def user(username):
    print username
    print User.query.filter_by(username=username).first()
    user = User.query.filter_by(username=username).first_or_404()
    skills = user.skills.order_by(Skill.name.asc()).all()
    return render_template('user.html', user=user, skills=skills)


@main.route('/edit-profile', methods=['GET', 'POST'])
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
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
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

    return render_template('edit_profile.html', form=form, user=user)

@main.route('/edit-skills/<int:id>', methods=['GET', 'POST'])
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
        return render_template('edit_skills.html', user=user, skills=skills, user_skills=user_skills)

@main.route('/list-users')
@login_required
@permission_required(Permission.MANAGE_USERS)
def list_users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.member_since.desc()).paginate(page, per_page=NumPaginationItems, error_out=False)
    users = pagination.items
    return render_template('list_users.html', users=users, pagination=pagination)

@main.route('/delete-user/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def delete_user(id):
    user = User.query.get_or_404(id)

    if user.is_administrator():
        flash("Can not delete administrator!", 'error')
        abort(404)

    form = DeleteUserForm()
    if form.validate_on_submit() and form.delete.data:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('.list_users'))

    return render_template('delete_user.html', user=user, form=form)

@main.route('/search-users', methods=['GET', 'POST'])
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

        return render_template('search_users.html', form=form, users=users, pagination=pagination)

    return render_template('search_users.html', form=form)

@main.route('/skill/<name>')
def skill(name):
    skill = Skill.query.filter_by(name=name).first()
    if skill:
        return render_template('skill.html', skill=skill)
    else:
        flash('Skill not found', 'error')
        abort(404)

@main.route('/edit-skill/<name>', methods=['GET', 'POST'])
@permission_required(Permission.MANAGE_SKILLS)
def edit_skill(name):
    skill = Skill.query.filter_by(name=name).first()
    if skill:
        form = EditSkillForm()

        if form.validate_on_submit():
            skill.name = form.name.data
            skill.description = form.description.data
            db.session.add(skill)
            return redirect(url_for('.skill', name=skill.name))
        else:
            form.name.data = skill.name
            form.description.data = skill.description
            return render_template('edit_skill.html', form=form)
    else:
        flash('Skill not found', 'error')
        abort(404)

@main.route('/list-skills')
def list_skills():
    skills = Skill.query.order_by(Skill.name.asc()).all()
    return render_template('list_skills.html', skills=skills)