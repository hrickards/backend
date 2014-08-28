
from flask import Flask, request, abort, render_template, make_response
from flask.views import View
from flask.ext.login import login_user, current_user

import portality.models as models
import portality.util as util
from portality.core import app, login_manager

from portality.view.query import blueprint as query
from portality.view.stream import blueprint as stream
from portality.view.account import blueprint as account
from portality.view.api import blueprint as api


app.register_blueprint(query, url_prefix='/query')
app.register_blueprint(stream, url_prefix='/stream')
app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(api, url_prefix='/api')


@login_manager.user_loader
def load_account_for_login_manager(userid):
    out = models.Account.pull(userid)
    return out

@app.context_processor
def set_current_context():
    """ Set some template context globals. """
    return dict(current_user=current_user, app=app)

@app.before_request
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    if remote_user:
        user = models.Account.pull(remote_user)
        if user is not None:
            login_user(user, remember=False)
    # add a check for provision of api key
    elif 'api_key' in request.values:
        res = models.Account.query(q='api_key:"' + request.values['api_key'] + '"')['hits']['hits']
        if len(res) == 1:
            user = models.Account.pull(res[0]['_source']['id'])
            if user is not None:
                login_user(user, remember=False)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(401)
def unauthorised(e):
    return render_template('401.html'), 401
        

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/docs")
def docs():
    return render_template("docs.html")
    

# TODO: an incomplete start at a possible place to display stories
# this will actually probably be implemented first in the API
@app.route("/story/<sid>")
def story(sid):
    story = models.Record.pull(sid.replace('.json',''))
    if story is None: abort(404)
    if util.request_wants_json() or sid.endswith('.json'):
        resp = make_response( story.json )
        resp.mimetype = "application/json"
        return resp    
    else:
        return render_template("story.html", story=story.json)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=app.config['DEBUG'], port=app.config['PORT'])

