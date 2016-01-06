from . import db
import time

class Resource(db.Model):
    __tablename__ = 'Resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    image_url = db.Column(db.String, nullable=True)
    price_p_per = db.Column(db.Integer)         # price per period in euro
    reserv_per = db.Column(db.Integer)          # reservation period in minutes

    @property
    def reservation_period(self):
        if self.reserv_per:
            return time.strftime("%H:%M", time.gmtime(self.reserv_per*60))
        else:
            return ""