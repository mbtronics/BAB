from flask import render_template, redirect, url_for, abort
from flask.ext.login import login_required, current_user
from . import main
from .forms import SelectPaymentTypeForm, PayForm
from .. import db
from ..resourcemodels import Reservation
from ..usermodels import Permission, User
from ..paymentmodels import Payment

@main.route('/user/<int:id>/payments', methods=['GET', 'POST'])
@login_required
def payments(id):

    if id!=current_user.id and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(404)

    user = User.query.get_or_404(id)
    form = SelectPaymentTypeForm()
    if form.validate_on_submit():
        if form.type.data=='reservation':
            return redirect(url_for('.list_reservations', id=id))
        elif form.type.data=='membership':
            return redirect(url_for('.pay_membership', id=id))
        elif form.type.data=='custom':
            return redirect(url_for('.pay_custom', id=id))

    return render_template('payment/payments.html', user=user, form=form)


@main.route('/user/<int:id>/pay-membership', methods=['GET', 'POST'])
@login_required
def pay_membership(id):

    if not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(404)

    user = User.query.get_or_404(id)

    form = PayForm(amount=12, description='Membership %s' % user.name)
    if form.validate_on_submit():
        if form.amount.data and form.description.data:
            p = Payment(user=user, description=form.description.data, method=form.method.data,
                        type='membership', amount=form.amount.data)
            db.session.add(p)
            db.session.commit()
            return redirect(url_for('.pay_membership', id=user.id))

    payments = Payment.query.filter_by(user=user, type='membership').all()

    return render_template('payment/pay.html', type='membership', form=form, user=user, payments=payments)


@main.route('/user/<int:id>/pay-custom', methods=['GET', 'POST'])
@login_required
def pay_custom(id):

    if not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(404)

    user = User.query.get_or_404(id)

    form = PayForm(amount=0, description='Custom payment for %s' % user.name)
    if form.validate_on_submit():
        if form.amount.data and form.description.data:
            p = Payment(user=user, description=form.description.data, method=form.method.data,
                        type='custom', amount=form.amount.data)
            db.session.add(p)
            db.session.commit()
            return redirect(url_for('.pay_custom', id=user.id))

    payments = Payment.query.filter_by(user=user, type='custom').all()

    return render_template('payment/pay.html', type='membership', form=form, user=user, payments=payments)


@main.route('/user/<int:user_id>/pay-reservation/<int:reser_id>', methods=['GET', 'POST'])
@login_required
def pay_reservation(user_id, reser_id):

    if not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(404)

    reservation = Reservation.query.get_or_404(reser_id)
    if reservation.user_id!=user_id:
        abort(404)

    form = PayForm(amount=reservation.cost, description=reservation.reason)
    if form.validate_on_submit():
        if form.amount.data and form.description.data:
            p = Payment(user=reservation.user, description=form.description.data, method=form.method.data,
                        type='reservation', reservation=reservation, amount=form.amount.data)
            db.session.add(p)
            db.session.commit()
            return redirect(url_for('.pay_reservation', id=reser_id))

    payments = Payment.query.filter_by(reservation=reservation, user=reservation.user).all()

    return render_template('payment/pay.html', type='reservation', form=form, user=reservation.user, reservation=reservation, payments=payments)