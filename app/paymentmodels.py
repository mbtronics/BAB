from . import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'Payments'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(100), unique=False)
    type = db.Column(db.Enum(u'reservation', u'payment', u'custom'), index=True, nullable=False)
    method = db.Column(db.Enum(u'terminal', u'cash', u'online'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('Reservations.id'))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime(), default=datetime.utcnow)