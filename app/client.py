#!/usr/bin/env python
from __future__ import print_function

import json
import ssl
import urllib2
from base64 import b64encode
from urllib import urlencode
import yaml
from os import path

import util


_validate_ssl = True


class API(object):
    _headers = None
    _params = None
    _validate_ssl = None
    res = None

    def __init__(self, base_url):
        self.base_url = base_url
        self._headers = {}
        self._params = {}
        self.form_urlencoded()

    def form_urlencoded(self):
        return self.set_header('Content-Type',
                               'application/x-www-form-urlencoded')

    def application_json(self):
        return self.set_header('Content-Type', 'application/json')

    def accept_json(self):
        return self.set_header('Accept', 'application/json')

    def set_header(self, name, value):
        self._headers[name] = value
        return self

    def set_param(self, name, value):
        self._params[name] = value
        return self

    def set_params(self, params):
        self._params.update(params)
        return self

    # HTTP Helpers

    def get(self, url, *args, **kwargs):
        kwargs.update(method='GET')
        return self.make_request(url, *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        kwargs.update(method='DELETE')
        return self.make_request(url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        kwargs.update(method='PUT')
        return self.make_request(url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        kwargs.update(method='POST')
        return self.make_request(url, *args, **kwargs)

    def set_validate_ssl(self, validate_ssl):
        self._validate_ssl = validate_ssl
        return self

    def set_access_token(self, access_token):
        self._headers['Authorization'] = 'Bearer {0}'.format(access_token)
        return self

    def set_basic_auth(self, username, password):
        self._headers['Authorization'] = 'Basic {0}'.format(
            b64encode(':'.join([username, password])))
        return self

    def make_request(self, url, *args, **kwargs):
        url = '{0}/{1}'.format(self.base_url, url)

        # do the request
        method = str(kwargs.get('method', 'GET')).upper()
        headers = kwargs.get('headers', self._headers)
        params = kwargs.get('params', self._params)

        if len(args) > 0:
            url = url.format(*args)

        if method in ['GET', 'DELETE', 'HEAD']:
            if '?' not in url:
                url += '?' + urlencode(params)
            if '?' in url and '&' in url:
                url += '&' + urlencode(params)
            if url.endswith('?'):
                url += urlencode(params)

        # print(method, url, params, headers)

        try:
            ctx = ssl.create_default_context()
            if (self._validate_ssl is not None and not self._validate_ssl) or \
                    (self._validate_ssl is None and not _validate_ssl):
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

            req = urllib2.Request(url)
            for k, v in headers.items():
                req.add_header(k, v)
            if method is not None:
                req.get_method = lambda: str(method).upper()
            if method in ['POST', 'PUT', 'PATCH'] and params is not None:
                if 'Content-Type' in headers and \
                                'application/json' == headers['Content-Type']:
                    body = json.dumps(params)
                else:
                    body = urlencode(params)
                res = urllib2.urlopen(req, body, context=ctx)
            else:
                res = urllib2.urlopen(req, context=ctx)
        except urllib2.HTTPError as e:
            res = e

        self.res = Response(res)
        return self.res


class Response(object):
    def __init__(self, response):
        self._response = response
        self._response_text = response.read()
        self._response_parsed = None

        if self._response_text and self.is_json:
            try:
                self._response_parsed = json.loads(self._response_text)
            except ValueError as e:
                self._response_parsed = {}
                if response.getcode() == 200:
                    print(e)

        if not self._response_parsed:
            self._response_parsed = self._response_text

    @property
    def content_type(self):
        return self._response.info().get('content-type', 'application/json')

    @property
    def is_html(self):
        return 'text/html' == self.content_type

    @property
    def is_json(self):
        return 'application/json' == self.content_type

    def raise_error(self):
        raise Exception(self._response_text)

    def pretty(self):
        return json.dumps(self.data, indent=4)

    @property
    def has_error(self):
        return isinstance(self._response, urllib2.HTTPError) or \
               self._response_parsed is None

    @property
    def headers(self):
        return self._response.info()

    @property
    def data(self):
        self.assert_no_error()
        return self._response_parsed

    @property
    def result(self):
        return self.data['result']

    def assert_no_error(self):
        if self.has_error:
            return self.raise_error()


class Config(object):
    def __init__(self, config=None):
        self.validate_ssl = True
        self.org_name = None
        self.space_name = None
        self.autoscaler_api_url = None
        self.app_id = None
        self.space_id = None
        self.token = None
        self.secret = None
        if not config:
            import config
            config = config.__dict__
        self.__dict__.update(config)


class Autoscaler(API):

    def __init__(self, config=None):
        super(Autoscaler, self).__init__(config.autoscaler_api_url)
        self.config = config

    def get_apps(self, **kwargs):
        return self.make_request('apps',
                                 params=kwargs)

    def get_available_apps(self, **kwargs):
        return self.make_request('apps/available',
                                 params=kwargs)

    def get_app(self, app_id, **kwargs):
        return self.make_request('apps/{0}', app_id,
                                 params=kwargs)

    def get_space_config(self):
        return self.make_request('spaces/config')

    def delete_app(self, app_id):
        return self.make_request('apps/{0}', app_id, method='DELETE')

    def import_app(self, app_id, **kwargs):
        return self.make_request('apps/{0}', app_id, method='POST',
                                 params=kwargs)

    def update_app(self, app_id, **kwargs):
        return self.make_request('apps/{0}', app_id, method='PUT',
                                 params=kwargs)

    def scale_app(self, app_id, **kwargs):
        return self.make_request('apps/{0}/scale', app_id, method='POST',
                                 params=kwargs)

    def enable_app(self, app_id):
        return self.make_request('apps/{0}/enable', app_id, method='POST')

    def disable_app(self, app_id):
        return self.make_request('apps/{0}/disable', app_id, method='POST')

    def get_app_stats_history(self, app_id, **kwargs):
        return self.make_request('apps/{0}/stats/history', app_id,
                                 params=kwargs)

    def get_app_stats_current(self, app_id, **kwargs):
        return self.make_request('apps/{0}/stats/current', app_id,
                                 params=kwargs)

    def verify_user_session(self, session):
        return self.make_request('users/session',
                                 headers={'x-session': session},
                                 method='POST')

    def get_scaling_config_html(self, app_id, **kwargs):
        return self.make_request('apps/{0}/scaling_config.html', app_id,
                                 method='POST', params=kwargs)

    def signin(self, username, password):
        return super(Autoscaler, self).make_request(
            'signin',
            method='POST',
            params=dict(username=username, password=password))

    def register_space_by_id(self, space_id, user_id, token, a=1, b=2, c=3):
        return super(Autoscaler, self).make_request(
            'apps/register',
            method='POST',
            params=dict(token=token, space_id=space_id,
                        user_id=user_id, a=a, b=b, c=c))

    def delete_space_by_id(self, space_id, token, org_space_name):
        return super(Autoscaler, self).make_request(
            'spaces/{0}/delete',
            space_id,
            method='POST',
            params=dict(token=token, name=org_space_name))

    def register_app_with_space(self):
        data = json.dumps({
            'token': self.config.token,
            'app_id': self.config.app_id
        })
        return self.make_request('spaces/register', method='POST', headers={
            'x-registration-token': util.encode_signature(
                self.config.secret, data, 300, time=util.unix_time(), join='.')
        })

    def make_request(self, url, *args, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers'].update({
            'x-cf-space-id': self.config.space_id,
            'x-request-signature':
                util.encode_signature(
                    self.config.secret, self.config.token, 3600, join='.')
        })
        return super(Autoscaler, self).make_request(url, *args, **kwargs)


def set_validate_ssl(validate_ssl):
    global _validate_ssl
    _validate_ssl = validate_ssl


def get_autoscaler(config=None):
    config = get_config(config)
    return Autoscaler(config)\
        .set_validate_ssl(config.validate_ssl)


def get_config(config=None):
    if isinstance(config, Config):
        return config
    if hasattr(config, '__dict__'):
        config = config.__dict__
    return Config(config)


def assert_config_org_space(config=None):
    config = get_config(config)
    space_config = get_autoscaler(config).get_space_config().result
    if config.org_name != space_config['org_name'] or \
            config.space_name != space_config['space_name']:
        raise Exception(
            'Configured Organization / Space names do not match: {0} / {1}'
            .format(config.org_name, config.space_name))


def load_manifest(filename, dirname=None, extra_config=None):
    autoscaler_web_dir = dirname or path.normpath(
        path.join(path.dirname(path.abspath(__file__)), '..'))
    filename = path.join(autoscaler_web_dir, filename)
    with open(filename, 'r') as f:
        manifest = yaml.load(f)
    config = manifest['applications'][0]['env']
    validate_ssl = config.get('CFAS_VALIDATE_SSL', True)
    if isinstance(validate_ssl, basestring):
        validate_ssl = 'false' != validate_ssl
    config = {
        'autoscaler_api_url': config['CFAS_API_URL'],
        'token': config['CFAS_TOKEN'],
        'secret': config['CFAS_SECRET'],
        'validate_ssl': validate_ssl
    }
    if extra_config:
        config.update(extra_config)
    return config


if '__main__' == __name__:
    def main():
        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option('-s', '--space-id', dest='space_id')
        parser.add_option('-m', '--manifest', dest='manifest_filename')
        parser.add_option('-q', '--quiet', dest='quiet', action='store_true')
        parser.add_option('-a', '--app-id', dest='app_id', default='')
        parser.add_option('-d', '--manifest-dir',
                          dest='manifest_dir', default=None)
        parser.add_option('--ignore-ssl',
                          dest='ignore_ssl', action='store_true', default=False)
        parser.add_option('--args',
                          dest='args', default='')
        (options, args) = parser.parse_args()

        if not options.quiet:
            print('Using manifest ' + options.manifest_filename)

        config = load_manifest(
            options.manifest_filename,
            dirname=options.manifest_dir,
            extra_config={'space_id': options.space_id})

        if config['validate_ssl'] and options.ignore_ssl:
            set_validate_ssl(False)
        client = get_autoscaler(config)
        action_func = getattr(client, args[0])
        if options.args:
            args = {item.split('=')[0]: ''.join(item.split('=')[1:])
                    for item in options.args.split('&')}
        else:
            args = {}

        if options.app_id:
            res = action_func(options.app_id, **args)
        else:
            res = action_func(**args)

        if res.is_json:
            print(json.dumps(res.data, indent=2))
        else:
            print(res.data)
    main()
