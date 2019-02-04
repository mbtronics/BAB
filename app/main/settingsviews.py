from flask import flash, render_template

from . import main
from .. import db
from ..decorators import permission_required
from ..settingsmodels import Setting
from ..usermodels import Permission
from .forms import ChangeSettingsForm

settings = ['invoice_details', 'vat_number', 'invoice_email']

@main.route('/settings', methods=['GET', 'POST'])
@permission_required(Permission.CHANGE_SETTINGS)
def change_settings():
    form = ChangeSettingsForm()
    if form.validate_on_submit():
        for setting in settings:
            value = getattr(form, setting)
            if value:
                s = Setting.query.filter_by(name=setting).first()
                if not s:
                    s = Setting(name=setting)
                s.value = value.data
                db.session.add(s)

        flash('New settings saved!')

    for setting in settings:
        s = Setting.query.filter_by(name=setting).first()
        if s:
            x=getattr(form, setting)
            x.__setattr__('data', s.value)

    return render_template('settings/change.html', form=form)
