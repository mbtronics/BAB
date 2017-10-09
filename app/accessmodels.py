from . import db


class Lock(db.Model):
    __tablenname__ = 'Locks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)


UserLocks = db.Table('UserLocks',
    db.Column('user_id', db.Integer, db.ForeignKey('Users.id')),
    db.Column('lock_id', db.Integer, db.ForeignKey('Locks.id'))
    )