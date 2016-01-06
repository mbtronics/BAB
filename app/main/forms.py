from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, IntegerField
from wtforms.validators import Required, Optional, Length, Email, Regexp, URL
from wtforms import ValidationError
from ..usermodels import Role, User, Skill


class EditProfileForm(Form):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Update information')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class DeleteConfirmationForm(Form):
    delete = BooleanField('Are you sure?')
    deletebutton = SubmitField('Delete')


class SearchUserForm(Form):
    name = StringField('Name', validators=[Optional()])
    id = IntegerField('Id', validators=[Optional()])
    searchbutton = SubmitField('Search')

class EditSkillForm(Form):
    name = StringField('Name', validators=[Required()])
    description = TextAreaField('Description', validators=[Required()])
    submit = SubmitField('Update skill')

class EditResourceForm(Form):
    name = StringField('Name', validators=[Required()])
    description = TextAreaField('Description', validators=[Required()])
    active = BooleanField('Active', validators=[Required()])
    image_url = StringField('Image URL', validators=[Optional(), URL()])
    price_p_per = IntegerField('Price per period', validators=[Optional()])
    reserv_per = IntegerField('Reservation period (minutes)', validators=[Optional()])
    submit = SubmitField('Update resource')