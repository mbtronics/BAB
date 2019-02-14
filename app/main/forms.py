from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, file_allowed
from wtforms import (BooleanField, DateField, FloatField, IntegerField, StringField, SubmitField, TextAreaField,
                     ValidationError)
from wtforms.validators import InputRequired, Length, Optional, Regexp, Required

from .. import photos
from models.usermodels import User


class EditProfileFormBasic(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    organisation = StringField('Organisation or company')
    invoice_details = TextAreaField('Invoice details (name + address + VAT number)')
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')


class EditProfileForm(EditProfileFormBasic):
    submit = SubmitField('Update information')


class EditProfileAdminForm(EditProfileFormBasic):
    username = StringField('Username (only letters, numbers, dots or underscores, should start with a letter or number)',
                           validators=[Required(),
                                       Length(1, 64),
                                       Regexp('^[A-Za-z0-9][A-Za-z0-9_.]*$', 0,
                                              'Usernames must have only letters, numbers, dots or underscores and should start with a letter or number')])
    confirmed = BooleanField('Confirmed')
    moderator = BooleanField('Moderator (not applicable for the admin)')
    keycard = StringField('Keycard code')

    photo = FileField('Photo', validators=[Optional(), file_allowed(photos, "Images only!")])

    submit = SubmitField('Update information')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class DeleteConfirmationForm(FlaskForm):
    delete = BooleanField('Are you sure?')
    deletebutton = SubmitField('Delete')


class SearchUserForm(FlaskForm):
    name = StringField('Name', validators=[Optional()])
    id = IntegerField('Id', validators=[Optional()])
    searchbutton = SubmitField('Search')

class EditSkillForm(FlaskForm):
    name = StringField('Name', validators=[Required()])
    description = TextAreaField('Description', validators=[Required()])
    submit = SubmitField('Update skill')

class EditResourceForm(FlaskForm):
    name = StringField('Name', validators=[Required()])
    description = PageDownField('Description', validators=[Required()])
    active = BooleanField('Active', validators=[Optional()])
    skill_required = BooleanField('Skill required', validators=[Optional()])
    photo = FileField('Photo', validators=[Optional(), file_allowed(photos, "Images only!")])
    price_p_per = IntegerField('Price per period (euro)', validators=[InputRequired()])
    reserv_per = IntegerField('Reservation period (minutes)', validators=[Required()])
    submit = SubmitField('Update resource')

class RequestInvoiceForm(FlaskForm):
    invoice_details = TextAreaField('Invoice details (name + address + VAT number)')
    vat_exempt = BooleanField('Are you VAT exempted (vrijstelling van BTW)?', default=False)
    submit = SubmitField('Request invoice')

class ChangeSettingsForm(FlaskForm):
    invoice_details = TextAreaField('Invoice details (name + address)')
    vat_number = StringField('VAT number')
    invoice_email = StringField('Invoice e-mail')
    submit = SubmitField('Change settings')

class ExpenseNoteForm(FlaskForm):
    total = FloatField('Total cost', validators=[Required()])
    description = StringField('Description', validators=[Required()])
    bank_account = StringField('Bank account', validators=[Required()])
    date = DateField('Date (costs made on)', validators=[Required()], format='%d/%m/%Y')
    file = FileField('File', validators=[Required()])
    submit = SubmitField('Create expense note')

class PayExpenseNoteForm(FlaskForm):
    paid = BooleanField('Paid', validators=[Optional()])
    submit = SubmitField('Save')

class ExportPayementsForm(FlaskForm):
    start = DateField('Start date', validators=[Required()], format='%d/%m/%Y')
    end = DateField('End date', validators=[Required()], format='%d/%m/%Y')
    only_paid = BooleanField('Only paid', validators=[Optional()])
    submit = SubmitField('Export')
