from . import db
import time
from markdown import markdown
import bleach

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
    price_p_per = db.Column(db.Integer)         # price per period in euro
    reserv_per = db.Column(db.Integer)          # reservation period in minutes

    skills = db.relationship('Skill', secondary=SkillsResources, backref=db.backref('resources', lazy='dynamic'), lazy='dynamic')
    reservations = db.relationship('Reservation', backref='Resource', lazy='dynamic')

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
