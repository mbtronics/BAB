#!/usr/bin/env python

import os

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

if not os.getenv('APP_ADMIN') or\
    not os.getenv('FLASK_CONFIG') or\
    not os.getenv('SECRET_KEY'):
    raise Exception('Environment settings invalid!')

from app import create_app, db
from app.usermodels import User, Role, Permission
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default', os.getenv('APP_URL_PREFIX') or '/')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Permission=Permission)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask.ext.migrate import upgrade
    from app.usermodels import Role

    upgrade()

    # create user roles
    Role.insert_roles()


def update_skill_resource_payments(skill, resource):
    print resource
    print skill

    num = 0
    for user in User.query.all():
        if user.has_skill(resource):
            num += 1
    print "num users: %d" % num

    for user in User.query.all():
        for payment in user.payments.filter_by(status='Paid').all():
            for payment_description in payment.paymentdescriptions:
                if payment_description.reservation and payment_description.reservation.resource==resource:
                    user.skills.append(skill)
                    break

    num = 0
    for user in User.query.all():
        if user.has_skill(resource):
            num += 1
    print "num users: %d" % num


def update_skill_resource_reservations(skill, resource):
    print resource
    print skill

    num = 0
    for user in User.query.all():
        if user.has_skill(resource):
            num += 1
    print "num users: %d" % num

    for user in User.query.all():
        for reservation in user.reservations:
            if reservation.resource==resource:
                user.skills.append(skill)
                break

    num = 0
    for user in User.query.all():
        if user.has_skill(resource):
            num += 1
    print "num users: %d" % num


@manager.command
def update_skills():
    from app.usermodels import User, Skill
    from app.resourcemodels import Resource

    resource = Resource.query.get(1)
    skill = Skill.query.get(8)
    update_skill_resource_payments(skill, resource)

    resource = Resource.query.get(4)
    skill = Skill.query.get(3)
    update_skill_resource_reservations(skill, resource)

    resource = Resource.query.get(7)
    skill = Skill.query.get(3)
    update_skill_resource_reservations(skill, resource)

    resource = Resource.query.get(8)
    skill = Skill.query.get(3)
    update_skill_resource_reservations(skill, resource)

if __name__ == '__main__':
    manager.run()
