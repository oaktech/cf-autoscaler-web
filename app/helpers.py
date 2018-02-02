import json
from functools import wraps

from flask import Blueprint
from flask import Flask
from flask import Response
from flask import request

import util
from app import client
from models import App
from models import Model


def build(data, status_code=200):
    data = json.dumps({
        'error': None,
        'status_code': status_code,
        'result': util.to_dict(data),
    })
    return Response(
        data,
        status=status_code,
        content_type='application/json')


def failure(message, status_code=400):
    data = json.dumps({
        'error': str(message),
        'status_code': status_code,
        'result': None,
    })
    return Response(
        data,
        status=status_code,
        content_type='application/json')


def success():
    return build(None)


def created(data):
    return build(data, 201)


def assert_app_exists(func):
    @wraps(func)
    def wrapped_f(app_id):
        app = App.find_by_id(app_id, use_cache=False)
        if not app:
            raise ApiError('App not found.', 404)
        return func(app)
    return wrapped_f


def assert_app_enabled(func):
    @wraps(func)
    def wrapped_f(app):
        if not app.enabled:
            raise ApiError('App is not enabled.', 403)
        return func(app)
    return wrapped_f


def is_logged_in():
    session_token = request.cookies.get('session', None)
    if not session_token:
        return False
    resp = client.get_autoscaler().verify_user_session(session_token)
    if resp.has_error:
        print(resp._response_text)
        return False
    user_data = resp.result
    setattr(request, 'user', user_data)
    return True


class ApiError(Exception):
    status_code = None
    message = None

    def __init__(self, message, status_code=400):
        super(ApiError, self).__init__()
        self.status_code = status_code
        self.message = message

    def to_response(self):
        return failure(self.message, self.status_code)


class CustomFlask(Flask):
    _wrapped_parse = {}

    def __init__(self, *args, **kwargs):
        super(CustomFlask, self).__init__(*args, **kwargs)

        @self.errorhandler(ApiError)
        def api_error(error):
            return error.to_response()

    def route(self, rule, **options):
        """
        This wrapper around `route()` does some type checking and pre parsing
         on the return result from a route function. If a dict, list or custom
         object is returned, the result will automatically be wrapped in a JSON
         response.

        :param rule:
        :param options:
        :return:
        """
        # Call the parent to get the real decorator.
        dec = super(CustomFlask, self).route(rule, **options)

        def dec2(f):
            #
            # "f" is the route function to be wrapped.
            #
            # We have to check if we have previously decorated this route
            # function because if it has been decorated previously, we need to
            # use that previously decorated function. This is because if we call
            # this @route twice on a single endpoint function, Flask will
            # internally check if this route has been registered before, and if
            # it has been registered, will verify that the "reference" of "f" is
            # identical to the previously registered function; if they are not
            # identical, Flask will throw an error.
            if f.__name__ in self._wrapped_parse:
                # If we've already registered this action name before, then
                # return the wrapper function we previously created.
                parse = self._wrapped_parse[f.__name__]
            else:
                # Here we define a wrapper function that calls the route
                # function "f" and does additional type checking and response
                # building.
                @wraps(f)
                def parse(*args, **kwargs):
                    # Call the route function and get the result
                    result = f(*args, **kwargs)
                    # Check the type of result to see if we can automatically
                    # create a response object for it.
                    if result is None:
                        result = success()
                    elif isinstance(result, (dict, list, Model)):
                        result = build(result)
                    return result
                # Since Flask internally relies on the __name__ property of
                # route functions, we need to pretend that our "parse" function
                # is the original route function, so that Flask will register
                # and call it properly
                parse.__name__ = f.__name__
                # We keep our own register of wrapped functions here, so that we
                # can reuse functions that are wrapped more than once with
                # different routes.
                self._wrapped_parse[parse.__name__] = parse

            # Finally we invoke the original "route" decorator function on our
            # wrapper function.
            return dec(parse)

        return dec2
