from . import db, login_manager
from flask.ext.login import UserMixin, AnonymousUserMixin
from datetime import datetime
from flask import current_app, request
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import thumb
from paymentmodels import PaymentDescription, Payment


#Bit-style permissions
class Permission:
    BOOK =              (1<<0)
    MANAGE_USERS =      (1<<1)
    MANAGE_SKILLS =     (1<<2)
    MANAGE_RESOURCES =  (1<<3)
    MANAGE_RESERVATIONS=(1<<4)
    MANAGE_PAYMENTS =   (1<<5)
    ADMINISTER =        0xffff

roles = {
    'User': (Permission.BOOK, True),
    'Moderator': (Permission.BOOK | Permission.MANAGE_USERS | Permission.MANAGE_SKILLS |
                  Permission.MANAGE_RESOURCES | Permission.MANAGE_RESERVATIONS | Permission.MANAGE_PAYMENTS, False),
    'Administrator': (Permission.ADMINISTER, False)
}

class Role(db.Model):
    __tablename__ = 'Roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')


    @staticmethod
    def insert_roles():
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Skill(db.Model):
    __tablename__ = 'Skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.Text(), nullable=False)

    @property
    def num_users(self):
        if self.users:
            return self.users.count()
        else:
            return 0

    def __repr__(self):
        return '<SkillType %r>' % self.name


UserSkills = db.Table('UserSkills',
    db.Column('user_id', db.Integer, db.ForeignKey('Users.id')),
    db.Column('skill_id', db.Integer, db.ForeignKey('Skills.id'))
    )


class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('Roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    photo_filename = db.Column(db.String(100))
    organisation = db.Column(db.String(50))
    invoice_details = db.Column(db.Text())

    skills = db.relationship('Skill', secondary=UserSkills, backref=db.backref('users', lazy='dynamic'), lazy='dynamic')
    reservations = db.relationship('Reservation', backref='user', lazy='dynamic')
    availability = db.relationship('Available', backref='user', lazy='dynamic')
    payments = db.relationship('Payment', backref='user', lazy='dynamic', foreign_keys=[Payment.user_id])
    payments_made = db.relationship('Payment', backref='operator', lazy='dynamic', foreign_keys=[Payment.operator_id])

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['APP_ADMIN']:
                self.role = Role.query.filter_by(permissions=Permission.ADMINISTER).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        else:
            return False

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def is_moderator(self):
        if self.is_administrator():
            return True
        else:
            return self.role.name=='Moderator'

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def photo_url(self, size=100):
        if self.photo_filename:
            thumb_url=thumb.thumbnail(self.photo_filename, '%dx%d' % (size, size))
            if thumb_url:
                return '/' + thumb_url

        return self.gravatar(size)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @property
    def membership_days_left(self):
        payment = db.session.query(Payment).filter(Payment.user==self)\
                    .join(PaymentDescription, Payment.id==PaymentDescription.payment_id)\
                    .filter(PaymentDescription.type=='membership')\
                    .order_by(Payment.date.desc()).first()
        if payment:
            left = 365-(datetime.utcnow()-payment.date).days
            if left>0:
                return left

        return 0

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

