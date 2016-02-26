from flask import render_template, redirect, url_for, abort, flash, request, session
from flask.ext.login import login_required, current_user
from sqlalchemy import or_
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, DeleteConfirmationForm, SearchUserForm
from .. import db
from ..usermodels import Permission, Role, User, Skill, Payment, PaymentDescription
from ..resourcemodels import Reservation
from ..decorators import permission_required, admin_required
from sqlalchemy import func
from .. import photos

NumPaginationItems = 20

@main.route('/user/<username>')
@login_required
def user(username):
    try:
        id = int(username)
        user = User.query.filter_by(id=id).first_or_404()
    except:
        user = User.query.filter_by(username=username).first_or_404()

    if user==current_user or \
       current_user.can(Permission.MANAGE_USERS) or \
       user.is_moderator():

        skills = user.skills.order_by(Skill.name.asc()).all()
        return render_template('user/view.html', user=user, skills=skills)

    abort(403)

def profile_form_to_user(form, user):
    user.name = form.name.data
    user.location = form.location.data
    user.about_me = form.about_me.data
    user.organisation = form.organisation.data
    user.invoice_details = form.invoice_details.data

def user_to_profile_form(form, user):
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    form.organisation.data = user.organisation
    form.invoice_details.data = user.invoice_details

@main.route('/user/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        profile_form_to_user(form, current_user)
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))

    user_to_profile_form(form, current_user)
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
        profile_form_to_user(form, user)
        user.username = form.username.data
        user.confirmed = form.confirmed.data

        if not user.is_administrator():
            if form.moderator.data:
                user.role = Role.query.filter_by(name='Moderator').first()
            else:
                user.role = Role.query.filter_by(name='User').first()

        if form.photo.data.filename:
            user.photo_filename = photos.save(form.photo.data)

        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))

    user_to_profile_form(form, user)

    form.username.data = user.username
    form.confirmed.data = user.confirmed

    if user.role.name=='Moderator':
        form.moderator.data = True
    else:
        form.moderator.data = False

    return render_template('user/edit.html', form=form, user=user)

@main.route('/user/<int:id>/edit-skills', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def edit_user_skills(id):
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
@admin_required
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

@main.route('/user/<int:id>/webcam', methods=['GET', 'POST'])
@login_required
def webcam(id):

    if id!=current_user.id and not current_user.can(Permission.MANAGE_USERS):
        abort(404)

    user = User.query.get_or_404(id)

    if request.method == 'POST':
        file = request.files['webcam']
        if file:
            user.photo_filename = photos.save(file)
            return ""

    return render_template('user/webcam.html', user=user)

@main.route('/user/<int:id>/reservations', methods=['GET'])
@login_required
def list_reservations(id):

    if id!=current_user.id and not current_user.can(Permission.MANAGE_USERS):
        abort(404)

    user = User.query.get_or_404(id)
    reservations = user.reservations.order_by(Reservation.start.desc()).all()

    return render_template('user/reservations.html', user=user, reservations=reservations)


@main.route('/user/stats')
@login_required
@permission_required(Permission.MANAGE_USERS)
def user_stats():

    total_users = User.query.count()
    paying_users = db.session.query(Payment)\
                    .join(PaymentDescription, Payment.id==PaymentDescription.payment_id)\
                    .filter(PaymentDescription.type=='membership').count()
    total_reservations = Reservation.query.count()
    total_revenue = round(db.session.query(func.sum(Payment.amount)).first()[0],2)

    return render_template('user/stats.html',   total_users=total_users, paying_users=paying_users,
                                                total_reservations=total_reservations, total_revenue=total_revenue)
