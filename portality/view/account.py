import uuid, json, time

from flask import Blueprint, request, url_for, flash, redirect, make_response
from flask import render_template, abort
from flask.ext.login import login_user, logout_user, current_user
from flask_wtf import Form
from wtforms.fields import TextField, TextAreaField, SelectField, HiddenField, PasswordField, BooleanField
from wtforms import validators, ValidationError

from portality.core import app
import portality.models as models
import portality.util as util

blueprint = Blueprint('account', __name__)


if len(app.config.get('SUPER_USER',[])) > 0:
    firstsu = app.config['SUPER_USER'][0]
    if models.Account.pull(firstsu) is None:
        su = models.Account(id=firstsu)
        su.set_password(firstsu)
        su.data['api_key'] = firstsu
        su.save()
        print 'superuser account named - ' + firstsu + ' created.'
        print 'default password matches username. Change it.'


@blueprint.route('/')
def index():
    if current_user.is_anonymous():
        abort(401)
    users = models.Account.query() #{"sort":{'id':{'order':'asc'}}},size=1000000
    if users['hits']['total'] != 0:
        accs = [models.Account.pull(i['_source']['id']) for i in users['hits']['hits']]
        # explicitly mapped to ensure no leakage of sensitive data. augment as necessary
        users = []
        for acc in accs:
            user = {'id':acc.id}
            if 'created_date' in acc.data:
                user['created_date'] = acc.data['created_date']
            users.append(user)
    if util.request_wants_json():
        resp = make_response( json.dumps(users, sort_keys=True, indent=4) )
        resp.mimetype = "application/json"
        return resp
    else:
        return render_template('account/users.html', users=users)


@blueprint.route('/<username>', methods=['GET','POST', 'DELETE'])
def username(username):
    acc = models.Account.pull(username)
    if acc is None:
        acc = models.Account.pull_by_email(username)
        if acc is not None: return redirect('/account/' + acc.id)
    if acc is None:
        acc = models.Account.pull_by_api_key(username)
        if acc is not None: return redirect('/account/' + acc.id)

    if acc is None:
        abort(404)
    elif ( request.method == 'DELETE' or 
            ( request.method == 'POST' and 
            request.values.get('submit',False) == 'Delete' ) ):
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)
        else:
            acc.delete()
            flash('Account ' + acc.id + ' deleted')
            return redirect(url_for('.index'))
    elif request.method == 'POST':
        if current_user.id != acc.id and not current_user.is_super:
            abort(401)
        newdata = request.json if request.json else request.values
        if newdata.get('id',False):
            if newdata['id'] != username:
                acc = models.Account.pull(newdata['id'])
            else:
                newdata['api_key'] = acc.data['api_key']
        for k, v in newdata.items():
            if k not in ['submit','password']:
                acc.data[k] = v
        if 'password' in newdata and not newdata['password'].startswith('sha1'):
            acc.set_password(newdata['password'])
        acc.save()
        flash("Record updated")
        return render_template('account/view.html', account=acc)
    else:
        if util.request_wants_json():
            resp = make_response( 
                json.dumps(acc.data, sort_keys=True, indent=4) )
            resp.mimetype = "application/json"
            return resp
        else:
            if current_user.is_super and acc.id != current_user.id:
                flash('Hi ' + current_user.id + ' - as a super user you can view and edit this account page. Be careful...', 'warning')
            return render_template('account/view.html', account=acc)


def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if target == util.is_safe_url(target):
            return target

class RedirectForm(Form):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if self.next.data == util.is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))

class LoginForm(RedirectForm):
    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        password = form.password.data
        username = form.username.data
        user = models.Account.pull(username)
        if user is None:
            user = models.Account.pull_by_email(username)
        if user is not None and user.check_password(password):
            login_user(user, remember=True)
            flash('Welcome back.', 'success')
            return redirect('/account/' + user.id)
        else:
            flash('Incorrect username/password', 'error')
    if request.method == 'POST' and not form.validate():
        flash('Invalid form', 'error')
    return render_template('account/login.html', form=form)

@blueprint.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        un = request.form.get('un',"")
        account = models.Account.pull(un)
        if account is None: account = models.Account.pull_by_email(un)
        if account is None:
            flash('Sorry, your account username / email address is not recognised. Please contact us.')
        else:
            newpass = util.generate_password()
            account.set_password(newpass)
            account.save()

            to = [account.data['email'],app.config['ADMIN_EMAIL']]
            fro = app.config['ADMIN_EMAIL']
            subject = app.config.get("SERVICE_NAME","") + "password reset"
            text = "A password reset request for account " + account.id + " has been received and processed.\n\n"
            text += "The new password for this account is " + newpass + ".\n\n"
            text += "If you are the user " + account.id + " and you requested this change, please login now and change the password again to something of your preference.\n\n"
            
            text += "If you are the user " + account.id + " and you did NOT request this change, please contact us immediately.\n\n"
            try:
                util.send_mail(to=to, fro=fro, subject=subject, text=text)
                flash('Your password has been reset. Please check your emails.')
                if app.config.get('DEBUG',False):
                    flash('Debug mode - new password was set to ' + newpass)
            except:
                flash('Email failed.')
                if app.config.get('DEBUG',False):
                    flash('Debug mode - new password was set to ' + newpass)

    return render_template('account/forgot.html')


@blueprint.route('/logout')
def logout():
    logout_user()
    flash('You are now logged out', 'success')
    return redirect('/')


def existscheck(form, field):
    test = models.Account.pull(form.w.data)
    if test:
        raise ValidationError('Taken! Please try another.')

class RegisterForm(Form):
    w = TextField('Username', [validators.Length(min=3, max=25),existscheck])
    n = TextField('Email Address', [
        validators.Length(min=3, max=35), 
        validators.Email(message='Must be a valid email address')
    ])
    s = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('c', message='Passwords must match')
    ])
    c = PasswordField('Repeat Password')
    profession = TextField('profession')
    confirm_public = BooleanField()
    confirm_terms = BooleanField()
    mailing_list = BooleanField()

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if not app.config.get('PUBLIC_REGISTER',False) and not current_user.is_super:
        abort(401)
    form = RegisterForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        api_key = str(uuid.uuid4())
        account = models.Account(
            id=form.w.data, 
            email=form.n.data,
            profession=form.profession.data,
            confirm_public=form.confirm_public.data,
            confirm_terms=form.confirm_terms.data,
            mailing_list=form.mailing_list.data,
            api_key=api_key
        )
        account.set_password(form.s.data)
        account.save()
        time.sleep(1)
        user = models.Account.pull(account.id)
        login_user(user, remember=True)
        flash('Welcome to your account', 'success')
        return redirect('/account/' + account.id)
    if request.method == 'POST' and not form.validate():
        flash('Please correct the errors', 'error')
    return render_template('index.html', form=form)

