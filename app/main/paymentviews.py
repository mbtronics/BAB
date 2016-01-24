from flask import render_template, redirect, url_for, abort, request
from flask.ext.login import login_required, current_user
from . import main
from .. import db
from ..usermodels import Permission, User
from ..paymentmodels import Payment, PaymentDescription

@main.route('/user/<int:id>/payments', methods=['GET', 'POST'])
@login_required
def payments(id):

    if id!=current_user.id and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(404)

    user = User.query.get_or_404(id)

    if request.form:
        try:
            types = request.form.getlist('type[]')
            reservations = []
            for r in request.form.getlist('reservation[]'):
                try:
                    reservations.append(int(r))
                except:
                    reservations.append(0)
            descriptions = request.form.getlist('description[]')
            amounts = [float(a) for a in request.form.getlist('amount[]')]
        except Exception, e:
            print e
            abort(404)

        payments = []
        i = 0
        total = 0
        for type in types:
            payment = {
                'type': types[i],
                'reservation': reservations[i],
                'description': descriptions[i],
                'amount': amounts[i]
            }
            payments.append(payment)
            total = total + amounts[i]
            i+=1

        p = Payment(method=request.form.get('method'), user=user, amount=total)
        db.session.add(p)
        db.session.flush()
        for payment in payments:
            pd = PaymentDescription(payment_id=p.id, type=payment['type'], description=payment['description'], amount=payment['amount'])
            if payment['reservation'] and payment['reservation']!=0:
                pd.reservation_id = payment['reservation']
            db.session.add(pd)
        db.session.commit()

        return redirect(url_for('.payment', id=p.id))

    methods = [val for val in Payment.method.property.columns[0].type.enums]
    return render_template('payment/pay.html', user=user, methods=methods)


@main.route('/payment/<int:id>', methods=['GET', 'POST'])
@login_required
def payment(id):

    p = Payment.query.get_or_404(id)
    if p.user!=current_user and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(403)

    descriptions = p.paymentdescriptions.all()
    return render_template('payment/payment.html', user=p.user, payment=p, descriptions=descriptions)