'''
The contentmine API.
'''

import json, urllib2, uuid

from flask import Blueprint, request, abort, make_response, redirect
from flask.ext.login import current_user

from portality.view.query import query as query
import portality.models as models
from portality.core import app
import portality.util as util

from datetime import datetime

from functools import wraps
from flask import g, request, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function
    
    
blueprint = Blueprint('api', __name__)


# return the API endpoint
@blueprint.route('/', methods=['GET','POST'])
@util.jsonp
def api():
    resp = make_response( json.dumps({
        "README": {
            "description": "Welcome to the openaccessbutton API.",
            "documnetation": "http://oabutton.cottagelabs.com/docs",
            "version": "2.0 - once it is ready"
        }
    }) )
    resp.mimetype = "application/json"
    return resp


@blueprint.route('/register', methods=['GET','POST'])
@util.jsonp
def register():
    try:
        # list the acceptable keys of a user object
        keys = ["username","name","email","profession","password"]
        # TODO: this should perhaps just call the account register functionality...
        # or account register should be dropped - have to check and see which is most suitable
        # check if account already exists and if so abort
        # TODO: this should explain why it is aborting
        exists = models.Account.pull(request.json.get('email',''))
        if exists is not None:
            resp = make_response(json.dumps({'errors': ['username already exists']}))
            resp.mimetype = "application/json"
            return resp, 400
        user = models.Account()
        for k in request.json.keys():
            # TODO: leaving this unchecked for now so we can test passing anything in
            #if k not in keys:
            #    abort(500)
            #else:
            user.data[k] = request.json[k]
        if 'username' not in user.data:
            user.data['username'] = user.data['email']
        user.data['id'] = user.data['username']
        user.data['api_key'] = str(uuid.uuid4())
        # TODO: this should set a random 8 digit password string if one is not provided by the register API call
        user.set_password(request.json.get('password',"password"))
        user.save()
        # TODO: trigger email account verification request
        resp = make_response(json.dumps({'api_key': user.data['api_key'], 'username': user.data['username']}))
        resp.mimetype = "application/json"
        return resp, 400
    except Exception, e:
        resp = make_response(json.dumps({'errors': [str(e)]}))
        resp.mimetype = "application/json"
        return resp, 400


@blueprint.route('/blocked', methods=['GET','POST'])
@util.jsonp
@login_required
def blocked():
    try:
        event = models.Record()
        event.data['coords_lat'] = request.values['coords_lat']
        event.data['coords_lng'] = request.values['coords_lng']
        event.data['accessed'] = datetime.datetime.now() # TODO: can this be dropped cos model does stuff anyway
        event.data['doi'] = request.values['doi']
        event.data['url'] = request.values['url']
        event.data['user_id'] = current_user.id
        event.data['user_email'] = current_user.data['email']
        event.data['user_name'] = current_user.data['name']
        event.data['user_profession'] = current_user.data['profession']
        event.save()
        return ""
    except Exception, e:
        resp = make_response(json.dumps({'errors': [str(e)]}))
        resp.mimetype = "application/json"
        return resp, 400


@blueprint.route('/oa_status', methods=['GET','POST'])
@util.jsonp
@login_required
def oa_status():
    try:
        url = request.values['url']
    
        # TODO: see code from old repo that finds the best alternate URL
        #open_url = best_open_url(url)
        result = {'status': 'ok'}
        '''if open_url is not None:
            result.update({'open_url': open_url})
        else:
            result.update({'open_url': ''})
        result.update({'blocked_count': OAEvent.objects.filter(url=url).count()})'''
    
        resp = make_response(json.dumps(result))
        resp.mimetype = "application/json"
        return resp

    except Exception, e:
        resp = make_response(json.dumps({'errors': [str(e)]}))
        resp.mimetype = "application/json"
        return resp, 400

