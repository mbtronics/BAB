from flask import render_template, redirect, url_for, abort, request, flash
from flask.ext.login import login_required, current_user
from . import main
from .. import db
from ..usermodels import Permission, User
from ..paymentmodels import Payment, PaymentDescription
from ..decorators import permission_required

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
        db.session.add(p)
        db.session.flush()
        for payment in payments:
            pd = PaymentDescription(payment_id=p.id, type=payment['type'], description=payment['description'], amount=payment['amount'])
            if payment['type']=='reservation' and payment['reservation'] and payment['reservation']!=0:
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


@main.route('/payment/<int:id>/invoice', methods=['GET', 'POST'])
@login_required
def payment_invoice(id):
    p = Payment.query.get_or_404(id)
    if p.user!=current_user and not current_user.can(Permission.MANAGE_PAYMENTS):
        abort(403)

    if not p.user.invoice_details or p.user.invoice_details=='':
        flash('User does not have invoice details, please edit user profile')
        return redirect(url_for('.payment', id=id))

    descriptions = p.paymentdescriptions.all()
    return render_template('payment/payment_invoice.html', user=p.user, payment=p, descriptions=descriptions)


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