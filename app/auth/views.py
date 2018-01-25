from flask import render_template, redirect, request, url_for, flash, abort, current_app
from flask.ext.login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..usermodels import User, Permission
from ..accessmodels import Lock
from ..email import send_email
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5] != 'auth.' and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():

        if form.organisation.data and form.organisation.data=='google':
            abort(404)

        if form.email.data \
                and form.email.data.endswith('.ru') \
                or form.email.data.endswith('.xyz') \
                or form.email.data.endswith('baburn.com'):
            abort(404)

        user = User(email=form.email.data,
                    username=form.username.data,
                    name=form.first_name.data + " " + form.last_name.data,
                    password=form.password.data)
        if form.organisation.data != "":
            user.organisation = form.organisation.data
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@auth.route('/confirm/<int:id>')
@login_required
def resend_confirmation(id=None):
    if id:
        user = User.query.get_or_404(id)

        if user!=current_user and not current_user.can(Permission.MANAGE_USERS):
            abort(404)
    else:
        user = current_user

    token = user.generate_confirmation_token()
    send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)
    flash('A new confirmation email has been sent to %s' % user.email)
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
    return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password', 'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('An email with instructions to reset your password has been sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            if not user.confirmed:
                user.confirmed = True
                db.session.add(user)
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            flash('Error while updating password.')
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address', 'auth/email/change_email',
                       user=current_user, token=token)
            flash('An email with instructions to confirm your new email address has been sent to you.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.index'))


@auth.route('/lock/<string:key>/<int:lock_id>/<int:keycard>')
def auth_lock(key, lock_id, keycard):

    if key!=current_app.config['LOCKS_KEY']:
        abort(401)

    user = User.query.filter_by(keycard=int(keycard)).first()
    if not user:
        abort(401)

    lock = Lock.query.get_or_404(lock_id)

    if lock in user.locks.all():
        return current_app.config['LOCKS_KEY']

    abort(401)