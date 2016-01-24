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
    

if __name__ == '__main__':
    manager.run()
