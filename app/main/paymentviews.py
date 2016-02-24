from flask import render_template, redirect, url_for, abort, request, current_app
from flask.ext.login import login_required, current_user
from . import main
from .. import db
from ..usermodels import Permission, User
from ..paymentmodels import Payment, PaymentDescription
from ..decorators import permission_required

import Mollie, time

NumPaginationItems = 20

def make_mollie_payment(p):
    mollie = Mollie.API.Client()
    mollie.setApiKey(current_app.config['MOLLIE_KEY'])
    payment = mollie.payments.create({
        'amount': p.amount,
        'description': 'BUDA::lab payment',
        'webhookUrl':  url_for('.mollie_webhook', id=p.id, _external=True, _scheme="https"),
        'redirectUrl': url_for('.mollie_redirect', id=p.id, _external=True, _scheme="https"),
        'metadata': {'order_nr': p.id}
    })
    return redirect(payment.getPaymentUrl())

@main.route('/payment/user/<int:id>', methods=['GET', 'POST'])
@login_required
def make_payment(id):
    if id!=current_user.id and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(404)

    user = User.query.get(id)

    if request.form:
        try:
            types = request.form.getlist('type[]')

            if user:
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
                'description': descriptions[i],
                'amount': amounts[i]
            }
            if user:
                payment['reservation'] = reservations[i]
            else:
                payment['reservation'] = None
            payments.append(payment)
            total = total + amounts[i]
            i+=1

        p = Payment(method=request.form.get('method'), user=user, amount=total, operator=current_user)
        if p.method=='cash' or p.method=='terminal':
            p.paid = True
        elif p.method=='online':
            p.paid = False
        else:
            abort(404)

        db.session.add(p)
        db.session.flush()
        for payment in payments:
            pd = PaymentDescription(payment_id=p.id, type=payment['type'], description=payment['description'], amount=payment['amount'])
            if payment['type']=='reservation' and payment['reservation'] and payment['reservation']!=0:
                pd.reservation_id = payment['reservation']
            db.session.add(pd)
        db.session.commit()

        if p.method == 'online':
            return make_mollie_payment(p)

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


@main.route('/payment/all')
@login_required
@permission_required(Permission.MANAGE_PAYMENTS)
def list_payments():
    page = request.args.get('page', 1, type=int)
    pagination = Payment.query.order_by(Payment.id.desc()).paginate(page, per_page=NumPaginationItems, error_out=False)
    payments = pagination.items
    return render_template('payment/list.html', payments=payments, pagination=pagination)


@main.route('/payment/new', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_PAYMENTS)
def anonymous_payment():
    return make_payment(0)


@main.route('/payment/mollie/webhook/<id>', methods=['GET', 'POST'])
def mollie_webhook(id):
    mollie = Mollie.API.Client()
    mollie.setApiKey(current_app.config['MOLLIE_KEY'])

    if 'id' not in request.form:
        print "id not in request.form"
        abort(404, 'Unknown payment id')

    payment_id = request.form['id']
    payment = mollie.payments.get(payment_id)
    order_nr = payment['metadata']['order_nr']

    print "mollie webhook, id=%s, order_nr=%s" % (payment_id, order_nr)

    if payment.isPaid():
        print 'Paid'
        p = Payment.query.get_or_404(order_nr)
        p.paid = True
    elif payment.isPending():
        # The payment has started but is not complete yet.
        print 'Pending'
    elif payment.isOpen():
        # The payment has not started yet. Wait for it.
        print 'Open'
    else:
        # The payment isn't paid, pending nor open. We can assume it was aborted.
        print 'Cancelled'

    return ('', 204)

@main.route('/payment/mollie/redirect/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_PAYMENTS)
def mollie_redirect(id):
    return redirect(url_for('.payment', id=id))
