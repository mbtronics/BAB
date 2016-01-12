from . import db
import time
from markdown import markdown
import bleach
import datetime

SkillsResources = db.Table('SkillsResources',
    db.Column('resource_id', db.Integer, db.ForeignKey('Resources.id')),
    db.Column('skill_id', db.Integer, db.ForeignKey('Skills.id'))
    )

class Resource(db.Model):
    __tablename__ = 'Resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text, nullable=False)
    description_html = db.Column(db.Text)
    active = db.Column(db.Boolean, nullable=False, default=False)
    image_url = db.Column(db.String, nullable=True)
    price_p_per = db.Column(db.Integer, default=0)         # price per period in euro
    reserv_per = db.Column(db.Integer, default=20)          # reservation period in minutes

    skills = db.relationship('Skill', secondary=SkillsResources, backref=db.backref('resources', lazy='dynamic'), lazy='dynamic')
    reservations = db.relationship('Reservation', backref='resource', lazy='dynamic')
    availability = db.relationship('Available', backref='resource', lazy='dynamic')

    @property
    def reservation_period(self):
        if self.reserv_per:
            return time.strftime("%H:%M", time.gmtime(self.reserv_per*60))
        else:
            return ""

    @staticmethod
    def on_changed_description(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.description_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                 tags=allowed_tags, strip=True))


db.event.listen(Resource.description, 'set', Resource.on_changed_description)

class Reservation(db.Model):
    __tablename__ = 'Reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), index=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('Resources.id'), index=True)
    start = db.Column(db.DateTime())
    end = db.Column(db.DateTime())
    reason = db.Column(db.String, nullable=True)
    paid = db.Column(db.Float, default=0)

    @property
    def duration(self):
        d=self.end-self.start
        hours, remainder = divmod(d.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return hours, minutes

    @property
    def duration_str(self):
        hours, minutes = self.duration
        duration_formatted = '%02d:%02d' % (hours, minutes)
        return duration_formatted

    @property
    def cost(self):
        hours, minutes = self.duration
        cost_per_minute = float(self.resource.price_p_per)/float(self.resource.reserv_per)
        return ((hours*60)+minutes)*cost_per_minute

class Available(db.Model):
    __tablename__ = "Availability"
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('Resources.id'), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), index=True)
    start = db.Column(db.DateTime())
    end = db.Column(db.DateTime())