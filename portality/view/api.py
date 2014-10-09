'''
The oabutton API.
'''

import json, urllib2, uuid, requests

from flask import Blueprint, request, abort, make_response, redirect
from flask.ext.login import current_user

from portality.view.query import query as query
import portality.models as models
from portality.core import app
import portality.util as util

from functools import wraps
from flask import g, request, redirect, url_for


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous():
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
        if request.json:
            vals = request.json
        else:
            vals = request.values
        # list the acceptable keys of a user object
        keys = ["username","name","email","profession","password"]
        # TODO: this should perhaps just call the account register functionality...
        # or account register should be dropped - have to check and see which is most suitable
        # check if account already exists and if so abort
        # TODO: this should explain why it is aborting
        exists = models.Account.pull(vals.get('email',''))
        if exists is not None:
            resp = make_response(json.dumps({'errors': ['username already exists']}))
            resp.mimetype = "application/json"
            return resp, 400
        user = models.Account()
        for k in vals.keys():
            # TODO: leaving this unchecked for now so we can test passing anything in
            #if k not in keys:
            #    abort(500)
            #else:
            user.data[k] = vals[k]
        if 'username' not in user.data:
            user.data['username'] = user.data['email']
        user.data['id'] = user.data['username']
        user.data['api_key'] = str(uuid.uuid4())
        # TODO: this should set a random 8 digit password string if one is not provided by the register API call
        user.set_password(vals.get('password',"password"))
        user.save()
        # TODO: trigger email account verification request
        resp = make_response(json.dumps({'api_key': user.data['api_key'], 'username': user.data['username']}))
        resp.mimetype = "application/json"
        return resp
    except Exception, e:
        resp = make_response(json.dumps({'errors': [str(e)]}))
        resp.mimetype = "application/json"
        return resp, 400


@blueprint.route('/retrieve', methods=['GET','POST'])
@util.jsonp
def retrieve():
    try:
        if request.json:
            vals = request.json
        else:
            vals = request.values
        exists = models.Account.pull_by_email(vals.get('email',''))
        if exists is not None:
            if exists.check_password(vals.get('password','')):
                resp = make_response(json.dumps({'api_key': exists.data['api_key']}))
                resp.mimetype = "application/json"
                return resp
            else:
                abort(401)
        else:
            abort(404)
    except Exception, e:
        resp = make_response(json.dumps({'errors': [str(e)]}))
        resp.mimetype = "application/json"
        return resp, 400


@blueprint.route('/blocked', methods=['GET','POST'])
@blueprint.route('/blocked/<bid>', methods=['GET','POST'])
@util.jsonp
@login_required
def blocked(bid=None):
    if bid is not None:
        e = models.Blocked.pull(bid)
        if request.method == 'GET':
            resp = make_response( json.dumps( e.data ) )
            resp.mimetype = "application/json"
            return resp
        elif request.method == 'POST':
            if request.json:
                vals = request.json
            else:
                vals = request.values
            
    else:
        try:
            if request.json:
                vals = request.json
            else:
                vals = request.values
            event = models.Blocked()
            event.data['coords_lat'] = vals.get('coords_lat','')
            event.data['coords_lng'] = vals.get('coords_lng','')
            event.data['doi'] = vals.get('doi','')
            event.data['url'] = vals.get('url','')
            event.data['user_id'] = current_user.id
            event.data['user_name'] = current_user.data.get('username','')
            event.data['user_profession'] = current_user.data.get('profession','')
            event.save()
            resp = make_response( json.dumps( {'url':vals.get('url',''), 'id':event.id } ) )
            resp.mimetype = "application/json"
            return resp
        except Exception, e:
            resp = make_response(json.dumps({'errors': [str(e)]}))
            resp.mimetype = "application/json"
            return resp, 400

        
@blueprint.route('/blocked/wishlist', methods=['GET','POST'])
@util.jsonp
@login_required
def wishlist():
    try:
        if request.json:
            vals = request.json
        else:
            vals = request.values
        event = models.Blocked()
        event.data['coords_lat'] = vals.get('coords_lat','')
        event.data['coords_lng'] = vals.get('coords_lng','')
        event.data['doi'] = vals.get('doi','')
        event.data['url'] = vals.get('url','')
        event.data['user_id'] = current_user.id
        event.data['user_name'] = current_user.data.get('username','')
        event.data['user_profession'] = current_user.data.get('profession','')
        event.save()
        wish = models.Wishlist()
        wish.data['url'] = vals.get('url','')
        wish.data['user_id'] = current_user.id
        wish.save()
        resp = make_response( json.dumps( {'url':vals.get('url',''), 'id':wish.id } ) )
        resp.mimetype = "application/json"
        return resp
    except Exception, e:
        resp = make_response(json.dumps({'errors': [str(e)]}))
        resp.mimetype = "application/json"
        return resp, 400


@blueprint.route('/status', methods=['GET','POST'])
@util.jsonp
@login_required
def status():
    try:
        if request.json:
            vals = request.json
        else:
            vals = request.values
            
        url = vals.get('url',False)
        if not url: abort(404)
        
        result = {}
        # find out the block count for this url and anything else we already know about it
        result['blocked'] = models.Blocked.count(url)
        result['wishlist'] = models.Wishlist.count(url)
        
        # quickscrape the url via contentmine, unless it is already in contentmine
        cm = _contentmine(url)
        result['contentmine'] = cm
                
        # look for further information if not already known, by calling the core processor
        if 'title' in cm.get('metadata',{}):
            #TODO: make a proper ignore list and strip any non-az09 characters
            qv = " AND ".join([ i for i in cm['metadata']['title'].replace(',','').split(' ') if i not in ['and','or','in','of','the','for']])
            result['core'] = _core(qv)
        
        # academia.edu, researchgate, mendeley?
        # look via other processors if available, and if further info may still be useful
        # contentmine - put in the text miners I wrote to contentmine API, and can submit any articles for processing if not done already
        # oag - look for the article licensing criteria
        # oarr - find relevant repositories?
        # doaj - can query for journal article by doi or url and get back the article metadata including fulltext link
        # crossref - get some metadata?
        
        # TODO: save what gets found somewhere
        
        resp = make_response(json.dumps(result))
        resp.mimetype = "application/json"
        return resp

    except Exception, e:
        resp = make_response(json.dumps({'errors': [str(e)]}))
        resp.mimetype = "application/json"
        return resp, 400


# TODO: can expose specific status functions with their own route
@blueprint.route('/processor/core/<value>', methods=['GET','POST'])
@util.jsonp
@login_required
def core(value):
    try:
        resp = make_response(json.dumps( _core(value) ))
        resp.mimetype = "application/json"
        return resp
    except Exception, e:
        resp = make_response(json.dumps({'errors': [str(e)]}))
        resp.mimetype = "application/json"
        return resp, 400


@blueprint.route('/test/cleanup', methods=['GET','POST'])
@util.jsonp
def testcleanup():
    try:
        # get all accounts starting with test_ and delete them (which removes their blocks and wishlists too)
        r = models.Account.query(q='id:test_*', size=1000000)
        rs = []
        for u in r['hits']['hits']:
            rs.append(u['_source']['id'])
            a = models.Account.pull(u['_source']['id'])
            a.delete()
        resp = make_response(json.dumps( rs ))
        resp.mimetype = "application/json"
        return resp
    except Exception, e:
        resp = make_response(json.dumps({'errors': [str(e)]}))
        resp.mimetype = "application/json"
        return resp, 400


def _core(value):
    url = app.config['PROCESSORS']['core']['url'].rstrip('/') + '/'
    api_key = app.config['PROCESSORS']['core']['api_key']
    addr = url + value
    addr += "?format=json&api_key=" + api_key
    print addr
    response = requests.get(addr)
    try:
        data = response.json()
        result = {}
        if 'ListRecords' in data and len(data['ListRecords']) != 0:
            record = data['ListRecords'][0]['record']['metadata']['oai_dc:dc']
            result['record'] = record
            result['url'] = record["dc:source"]
            result['title'] = record["dc:title"]
            result['description'] = record["dc:description"]
        return result
    except:
        return {}


def _contentmine(value):
    # check to see if it is in contentmine
    url = app.config['PROCESSORS']['contentmine']['url'].rstrip('/') + '/'
    api_key = app.config['PROCESSORS']['contentmine'].get('api_key','')
    addr = url + 'processor/quickscrape?'
    addr += 'url=' + value + '&'
    addr += 'scraper=generic_open&'
    if api_key: addr += "api_key=" + api_key + '&'
    response = requests.get(addr)
    # if not get contentmine to quickscrape it
    # then return the metadata about it
    try:
        return response.json()
    except Exception, e:
        return {"errors": [str(e)]}




