#!/usr/bin/env python

import os

from app import util
from app.app import app
from app.app import socketio
import app.monitor as m
from app import config
from app import client

application = app

if __name__ == "__main__":
    client.set_validate_ssl(config.validate_ssl)
    client.assert_config_org_space()
    util.register_with_api()
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
