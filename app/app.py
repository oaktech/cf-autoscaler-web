from __future__ import print_function

import os
import json

from flask import Response
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask.ext.socketio import SocketIO
from models import App
import traceback
import client
import config
import helpers
import util

client.set_validate_ssl(config.validate_ssl)

app = helpers.CustomFlask(__name__)
app.debug = os.getenv('APP_DEBUG', 'false') == 'true'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', util.rand(16))

socketio = SocketIO(app)

routes_whitelist = [
    '/signin',
]


def form_as_dict():
    form = {}
    for key, val in request.form.items():
        if key not in form:
            form[key] = val
        elif not isinstance(form[key], list):
            form[key] = [form[key], val]
        else:
            form[key].append(val)
    return form


@app.context_processor
def inject_custom_jinja_vars():
    return dict(
        error_message=request.args.get('error', None),
        format_unix_time=util.format_unix_time,
        unix_time=util.unix_time,
        round=round,
        len=len,
        int=int,
        getattr=getattr,
        now=util.unix_time(),
        request=request,
    )


@app.before_request
def redirect_http_to_https():
    xfp = request.headers.get('x-forwarded-proto', None)
    if request.url.startswith('http://') and 'https' != xfp and xfp is not None:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

    if request.path in routes_whitelist:
        return

    if request.path.startswith(('/static/js/', '/static/css/', '/socket.io/')):
        return

    cli = client.get_autoscaler()

    session_token = request.args.get('t', None)
    if session_token:
        resp = cli.verify_user_session(session_token)
        if resp.has_error:
            print(resp._response_text)
            return redirect('/signin')

        resp = redirect(request.path)
        resp.set_cookie('session', session_token, secure=True)
        return make_response(resp)

    if not helpers.is_logged_in():
        return redirect('/signin')


@app.errorhandler(500)
@app.errorhandler(BaseException)
def error_500(e):
    print (traceback.format_exc())
    if request.path.startswith('/api/') or 'POST' == request.method.upper():
        e = util.parse_error_as_json(e)
        return Response(
            status=500,
            headers={
                'Content-Type': 'application/json'
            },
            response=json.dumps({
                'status_code': 500,
                'message': e
            }))
    return render_template('error.html',
                           title='Error 500',
                           message='Something went wrong... :(',
                           error_message=request.args.get(
                               'error', str(e)))


@app.errorhandler(404)
def error_404(e):
    return render_template('error.html',
                           title='Error 404',
                           message='Page Not Found')


@app.route('/signin', methods=['GET'])
def login():
    """Display the autoscaler signin page. Also receives the signin credentials
    from the signin form and verifies. If signin is successful, it will also
    redirect to the /authorize page to authorize the autoscaler with
    Cloud Foundry.
    """

    return redirect(
        config.autoscaler_api_url + '/apps/' + config.app_id + '/signin')


@app.route('/logout')
def logout():
    """Clear the user's session
    """
    resp = redirect('/signin')
    resp.set_cookie('session', '', secure=True)
    return resp


@app.route('/')
def list_my_apps():
    """Show a list of the user's apps imported for autoscaling. If no apps have
    been imported, then the user will be redirected to the /apps/available page
    to import apps.
    """
    my_apps = App.list_my_apps()
    if not my_apps:
        return redirect('/apps/available')
    if config.app_id is not None:
        my_apps = [app for app in my_apps if app.app_id != config.app_id]
    return render_template(
        'apps/list.html',
        apps=my_apps,
        is_available=False,
        title='Imported Apps')


@app.route('/apps/available')
def list_available_apps():
    """Checks with Cloud Foundry to display a list of all apps within the configured
    organization and space that have not yet been imported (hence available).
    """
    apps = App.list_available_apps()
    if config.app_id is not None:
        apps = [app for app in apps if app.app_id != config.app_id]
    return render_template(
        'apps/list.html',
        apps=apps,
        is_available=True,
        title='Available Apps')


def _load_app_view_details(app):
    scaling_num_instances = config.get_scaling_num_instances(app)
    autoscaler_name = request.form.get('autoscaler')
    scaling_config = client.get_autoscaler()\
        .get_scaling_config_html(app.app_id, autoscaler=autoscaler_name).data
    return dict(
        title=app.app_name,
        app=app,
        scaling_num_instances=scaling_num_instances,
        scaling_memory=config.scaling_memory,
        scaling_disk=config.scaling_disk,
        autoscaler_name=autoscaler_name,
        scaling_config=scaling_config)


@app.route('/apps/<app_id>')
@helpers.assert_app_exists
def view_app(app):
    """The page for monitoring app performance and adjusting autoscaling
    parameters.
    """
    kwargs = _load_app_view_details(app)
    return render_template('apps/view.html', **kwargs)


@app.route('/apps/<app_id>/scaling_config.html', methods=['POST'])
@helpers.assert_app_exists
def view_scaling_config(app):
    kwargs = _load_app_view_details(app)
    return Response(kwargs['scaling_config'], content_type='text/html')


@app.route('/apps/<app_id>/history')
@helpers.assert_app_exists
def view_history(app):
    return render_template('apps/history.html', app=app)


@app.route('/api/apps/<app_id>/history')
@helpers.assert_app_exists
def get_app_history(app):
    args = {}
    for key, value in request.args.items():
        args[key] = value
    result = app.get_history_stats(**args)
    return result


@app.route('/api/apps/<app_id>', methods=['POST'])
def import_app(app_id):
    cli = client.get_autoscaler()
    return cli.import_app(app_id).result


@app.route('/api/apps/<app_id>/scale', methods=['POST'])
def scale_app(app_id):
    cli = client.get_autoscaler()
    return cli.scale_app(app_id, **form_as_dict()).result


@app.route('/api/apps/<app_id>/save', methods=['POST'])
@helpers.assert_app_exists
def save_app(app):
    form = {key: val for key, val in request.form.items()}
    cli = client.get_autoscaler()
    return cli.update_app(app.app_id, **form).result


@app.route('/api/apps/<app_id>', methods=['DELETE'])
@helpers.assert_app_exists
def remove_app(app):
    return app.remove()


@app.route('/api/apps/<app_id>/enable', methods=['POST'])
@app.route('/api/apps/<app_id>/disable', methods=['POST'])
@helpers.assert_app_exists
def enable_app(app):
    if request.path.endswith('/enable'):
        app.save_enabled(enabled=True)
    elif request.path.endswith('/disable'):
        app.save_enabled(enabled=False)


@app.route('/config')
def view_config():
    """Displays a brief summary of the configuration data for this autoscaler.
    """
    cf_config = client.get_autoscaler().get_space_config().result
    return render_template('config.html', config=config, cf_config=cf_config)

