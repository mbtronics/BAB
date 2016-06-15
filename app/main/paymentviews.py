from flask import render_template, redirect, url_for, abort, request, flash
from flask.ext.login import login_required, current_user
from . import main
from .. import db, mollie
from ..usermodels import Permission, User
from ..paymentmodels import Payment, PaymentDescription
from ..decorators import permission_required
from ..email import send_email
from forms import RequestInvoiceForm
from ..settingsmodels import Setting

NumPaginationItems = 20

@main.route('/payment/user/<int:id>', methods=['GET', 'POST'])
@login_required
def make_payment(id):
    if id!=current_user.id and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(404)

    user = User.query.get(id)

    if request.form:
        try:
            types = request.form.getlist('type[]')

            if not types:
                flash("You can't make a payment without adding rows!")
                abort(500)

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
                if type=='reservation' and not payment['reservation']:
                    flash("You selected type reserveration without selecting an actual reservation!")
                    abort(500)
            else:
                payment['reservation'] = None
            payments.append(payment)
            total = total + amounts[i]
            i+=1

        if not total:
            flash("You can't make a payment without amounts!")
            abort(500)

        if user and not user.has_valid_membership and not 'membership' in types:
            flash("This user has no valid membership! Add a membership payment or payment will not work!")
            abort(500)

        method = request.form.get('method')
        if method=='credits' and user.credits<total:
            flash("User has not enough credits!")
            abort(500)

        p = Payment(method=method, user=user, amount=total, operator=current_user)

        db.session.add(p)
        db.session.flush()
        for payment in payments:
            pd = PaymentDescription(payment_id=p.id, type=payment['type'], description=payment['description'], amount=payment['amount'])
            if payment['type']=='reservation' and payment['reservation'] and payment['reservation']!=0:
                pd.reservation_id = payment['reservation']
            db.session.add(pd)

        if p.method=='cash' or p.method=='terminal':
            payment_verified(p)
        elif p.method=='online':
            p.status = 'Open'
        elif p.method=='credits':
            user.credits -= total
            payment_verified(p)
        else:
            abort(404)

        db.session.commit()

        if p.method == 'online':
            return redirect(url_for('.pay_with_mollie', id=p.id))

        return redirect(url_for('.payment', id=p.id))

    if user and not user.has_valid_membership:
        flash("This user has no valid membership! A membership payment is automatically added, payment will not work without!")
        force_membership = True
    else:
        force_membership = False

    # We can get the methods from the db model, but this way we can change the order
    #methods = [val for val in Payment.method.property.columns[0].type.enums]
    methods = [u'online', u'terminal', u'cash']
    return render_template('payment/pay.html', user=user, methods=methods, force_membership=force_membership)


@main.route('/payment/<int:id>', methods=['GET', 'POST'])
@login_required
def payment(id):
    p = Payment.query.get_or_404(id)
    if p.user!=current_user and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(403)

    descriptions = p.paymentdescriptions.all()
    return render_template('payment/payment.html', user=p.user, payment=p, descriptions=descriptions)


@main.route('/payment/<int:id>/proof', methods=['GET', 'POST'])
@login_required
def payment_proof(id):
    p = Payment.query.get_or_404(id)
    if p.user!=current_user and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(403)

    if not p.user:
        flash('Not possible for anonymous payment')
        abort(500)

    vat_number = Setting.query.get('vat_number')
    our_invoice_details = Setting.query.get('invoice_details')
    if not vat_number.value or not our_invoice_details.value:
        flash('Invoice settings incorrect!')
        abort(500)

    descriptions = p.paymentdescriptions.all()
    return render_template('payment/payment_proof.html', user=p.user, payment=p, descriptions=descriptions,
                           our_invoice_details=our_invoice_details, vat_number=vat_number)

@main.route('/payment/<int:id>/invoice', methods=['GET', 'POST'])
@login_required
def payment_invoice(id):
    p = Payment.query.get_or_404(id)
    if p.user!=current_user and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(403)

    if not p.user:
        flash('Not possible for anonymous payment')
        abort(500)

    descriptions = p.paymentdescriptions.all()

    invoice_email = Setting.query.get('invoice_email')
    if not invoice_email.value:
        flash('Invoice settings incorrect!')
        abort(500)

    form = RequestInvoiceForm()
    if form.validate_on_submit():
        send_email(invoice_email.value, 'Request invoice', 'payment/email/request_invoice',
                   payment=p, descriptions=descriptions, invoice_details=form.invoice_details.data, vat_exempt=form.vat_exempt.data)
        send_email(p.user.email, 'Invoice request pending', 'payment/email/request_invoice',
                   payment=p, descriptions=descriptions, invoice_details=form.invoice_details.data, vat_exempt=form.vat_exempt.data)
        flash("Your invoice request has been send. You should receive it by e-mail.")
        return redirect(url_for('.payment', id=id))

    form.invoice_details.data = p.user.invoice_details
    form.vat_exempt.data = False;

    return render_template('payment/request_invoice.html', user=p.user, payment=p, descriptions=descriptions, form=form)

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


@main.route('/payment/mollie/pay/<int:id>', methods=['GET'])
@login_required
def pay_with_mollie(id):
    if id!=current_user.id and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(404)

    p = Payment.query.get_or_404(id)
    payment = mollie.payments.create({
        'amount': p.amount,
        'description': 'BUDA::lab payment',
        'webhookUrl':  url_for('.mollie_webhook', _external=True, _scheme="https"),
        'redirectUrl': url_for('.mollie_redirect', id=p.id, _external=True, _scheme="https"),
        'metadata': {'order_nr': p.id}
    })
    return redirect(payment.getPaymentUrl())


@main.route('/payment/mollie/webhook', methods=['GET', 'POST'])
def mollie_webhook():
    if 'id' not in request.form:
        abort(404, 'Unknown payment id')

    mollie_id = request.form['id']
    payment = mollie.payments.get(mollie_id)
    order_nr = payment['metadata']['order_nr']
    p = Payment.query.get_or_404(order_nr)
    p.mollie_id = mollie_id

    if payment.isPaid():
        payment_verified(p)
    elif payment.isPending():
        p.status = 'Pending'
    elif payment.isOpen():
        p.status = 'Open'
    else:
        p.status = 'Cancelled'

    return ('', 204)


@main.route('/payment/mollie/redirect/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_PAYMENTS)
def mollie_redirect(id):
    return redirect(url_for('.payment', id=id))


def payment_verified(p):
    p.status = 'Paid'

    for pd in p.paymentdescriptions:
        if pd.type == 'credits':
            p.user.credits += pd.amount