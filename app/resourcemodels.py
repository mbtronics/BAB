from . import db

class Resource(db.Model):
    __tablename__ = 'Resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    image_url = db.Column(db.String, nullable=True)
    price_p_per = db.Column(db.Integer)         # price per period in euro
    reserv_per = db.Column(db.Integer)          # reservation period in minutes
    cons_name = db.Column(db.String(64))        # name for consumable
    cons_cost = db.Column(db.Integer)           # cost per unit for consumables
    cons_unit = db.Column(db.String(64))        # unit for consumables