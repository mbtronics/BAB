from . import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'Payments'
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.Enum(u'terminal', u'cash', u'online'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=True)
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime(), default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    status = db.Column(db.Enum('Open', 'Pending', 'Paid', 'Cancelled'), nullable=False, default='Open')
    mollie_id = db.Column(db.String(20))

    paymentdescriptions = db.relationship('PaymentDescription', backref='payment', lazy='dynamic')

    @property
    def paid(self):
        if self.status=='Paid':
            return True
        else:
            return False

class PaymentDescription(db.Model):
    __tablename__ = 'PaymentDescriptions'
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('Payments.id'), nullable=False)
    type = db.Column(db.Enum(u'reservation', u'membership', u'custom'), index=True, nullable=False) #Sync with pay.html
    description = db.Column(db.String(100), unique=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('Reservations.id'), nullable=True)
    amount = db.Column(db.Float)