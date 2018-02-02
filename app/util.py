import base64
import decimal
import hashlib
import hmac
import json
import random
import string
import time
from datetime import datetime
from decimal import Decimal

from dateutil import parser

import client

rand_chars = ''.join([string.digits, string.lowercase, string.uppercase])


def datetime_to_unix(dt):
    return int(time.mktime(dt.timetuple()))


def unix_time():
    return int(time.time())


def parse_unix_time(time_str):
    return datetime_to_unix(parser.parse(time_str))


def format_unix_time(unix, format):
    return datetime.fromtimestamp(int(unix)).strftime(format)


def to_json(objects):
    return json.dumps(to_dict(objects))


def to_dict(objects):
    if objects is None:
        return objects

    if isinstance(objects, dict):
        return {key: to_dict(value) for key, value in objects.items()}

    def obj_to_dict(obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return obj

    if isinstance(objects, list):
        return [obj_to_dict(item) for item in objects]
    else:
        return obj_to_dict(objects)


def rand(n):
    return ''.join(random.sample(rand_chars, n))


def get_hmac(secret):
    return hmac.new(bytearray(secret.encode('utf-8')), digestmod=hashlib.sha256)


def decode_signature(signature):
    signature = signature.split('.')
    signature[0] = base64.b64decode(signature[0])
    signature[1] = int(base64.b64decode(signature[1]))
    signature[2] = int(base64.b64decode(signature[2]))
    return signature


def encode_signature(secret, data, ttl, time=None, join=None):
    data = base64.b64encode(data.encode('utf-8'))
    t = base64.b64encode(str(time or unix_time()).encode('utf-8'))
    ttl = base64.b64encode(str(ttl).encode('utf-8'))
    params = [data, t, ttl]

    h = get_hmac(secret)
    h.update('|'.join(params))
    sig = base64.b64encode(h.digest())
    params.append(sig)
    if join:
        return join.join(params)
    return params


def valid_signature(secret, signature):
    signature = decode_signature(signature)
    token = signature[0]
    t = signature[1]
    ttl = signature[2]
    sig = encode_signature(secret, token, ttl, time=t)[3]
    return signature[3] == sig and (not ttl or (unix_time() < t + ttl))


def register_with_api():
    client.get_autoscaler().register_app_with_space().assert_no_error()


def parse_error_as_json(e):
    e = str(e).strip()
    if e.startswith('{') and e.endswith('}'):
        try:
            data = json.loads(e)
            print(data)
            if 'error' in data:
                e = data['error']
        except Exception as e2:
            print('Unable to parse error message as json')
    return e


class Stat:
    def __init__(self, precision=9):
        self.add_context = decimal.Context(prec=20,
                                           rounding=decimal.ROUND_HALF_EVEN)
        self.context = decimal.Context(prec=precision,
                                       rounding=decimal.ROUND_HALF_EVEN)
        self.sum = Decimal(0)
        self.sum2 = Decimal(0)
        self.count = 0

    def mean(self):
        with decimal.localcontext(self.context):
            if self.count < 1:
                return Decimal(0)

            return self.sum / Decimal(self.count)

    def variance(self):
        with decimal.localcontext(self.context):
            if self.count <= 1:
                return Decimal(0)

            count = Decimal(self.count)
            return (count * self.sum2 - (self.sum * self.sum)) / \
                   (count * (count - 1))

    def std(self):
        return self.variance().sqrt(self.context)

    def add(self, value):
        with decimal.localcontext(self.add_context):
            value = Decimal(value)
            self.sum += value
            self.sum2 += value * value
            self.count += 1
            return self
