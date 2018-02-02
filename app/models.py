from __future__ import print_function

import json

import client
import util


def _wrap(items, wrapper=None):
    if not wrapper:
        wrapper = Model
    if isinstance(items, list):
        return [wrapper(item) for item in items]
    return wrapper(items)


class Model(object):
    def __init__(self, row, opts=None):
        if isinstance(row, dict):
            for key in row:
                setattr(self, key, row[key])

    def __getitem__(self, item):
        return getattr(self, item)

    def __str__(self):
        return json.dumps(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {key: util.to_dict(value)
                for key, value in self.__dict__.items()}

    @classmethod
    def get_obj(cls, **kwargs):
        return cls(kwargs)

    @classmethod
    def wrap_dict(cls, d, opts=None):
        if d is None:
            return d
        return cls(d, opts)

    @classmethod
    def wrap_list(cls, list_of_dicts, opts=None):
        if list_of_dicts is None:
            return []
        return [cls.wrap_dict(row, opts) for row in list_of_dicts]


class App(Model):
    """This class models the `apps` table as well as a Cloud Foundry API App
    Object
    """

    app_id = None
    app_name = None
    space_id = None
    time_created = None
    enabled = None
    scaling_config = None

    state = None
    num_instances = None

    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        # self.scaling_config = \
        #     autoscaler.ScalingConfigFormatter(
        #         **args[0].get('scaling_config', {}))

    @property
    def url(self):
        return '/apps/' + self.app_id

    @property
    def history_url(self):
        return '/apps/' + self.app_id + '/history'

    def get_autoscaler_name(self):
        return self.scaling_config.get('autoscaler')

    # @property
    # def autoscaler(self):
    #     autoscaler_name = self.get_autoscaler_name()
    #     return autoscaler.load_module(autoscaler_name)

    # def get_new_autoscaler(self):
    #     autoscaler_module = self.autoscaler
    #     return autoscaler_module.Autoscaler(
    #         self.app_id, **self.scaling_config.get())

    # def get_new_autoscaler_form(self, form, autoscaler_name=None):
    #     if autoscaler_name:
    #         autoscaler_module = autoscaler.load_module(autoscaler_name)
    #     else:
    #         autoscaler_module = self.autoscaler
    #     form_has_data = len(form) > 0
    #     form = autoscaler_module.ScalingConfig(form)
    #     if not form_has_data:
    #         form.set_params(
    #             **self.scaling_config.get(autoscaler=autoscaler_name))
    #     return form

    def get_current_stats(self, **kwargs):
        """Gets the _list_ of Cloud Foundry performance metrics for each
        "instance" in the deployment for this app _directly_ from the
        Cloud Foundry API.

        Returns:
            list[AppStats]
        """
        stats = client.get_autoscaler() \
            .get_app_stats_current(self.app_id, **kwargs).result
        return _wrap(stats, AppStats)

    def get_history_stats(self, **kwargs):
        """Gets recently saved stats for this app from the database _not_ the
        Cloud Foundry API. Similar to `get_cf_stats`.

        Keyword Args:
            time_interval (int): the number of seconds before now to query for
                stats.
        """
        stats = client.get_autoscaler() \
            .get_app_stats_history(
                self.app_id, **kwargs).result
        return _wrap(stats, AppStats)

    def update_cf(self, **kwargs):
        """Updates the Cloud Foundry API with the properties in the `params`
        dict. See the Cloud Foundry API for valid parameter keys and values.
        "params" are passed _directly_ to the Cloud Foundry API.

        Keyword Args:
            dict

        Returns:
            dict
        """
        return client.get_autoscaler() \
            .update_app(self.app_id, **kwargs) \
            .assert_no_error()

    def create(self):
        """Saves a new "apps" table entry in the database for the app
        represented by this App-object.
        """
        if self.enabled is None:
            self.enabled = False
        client.get_autoscaler() \
            .import_app(self.app_id,
                        app_id=self.app_id,
                        app_name=self.app_name,
                        space_id=self.space_id,
                        time_created=util.unix_time(),
                        enabled=self.enabled)\
            .assert_no_error()
        return self

    def remove(self):
        """Removes this app entry from the "apps" table in the database.
        Does nothing else.
        """
        return client.get_autoscaler() \
            .delete_app(self.app_id).result

    def save_enabled(self, enabled=None):
        """Saves into the database whether this app is enabled for autoscaling or not.
        """
        self._assert_app_id()

        if isinstance(enabled, bool):
            cli = client.get_autoscaler()
            if enabled:
                resp = cli.enable_app(self.app_id)
            else:
                resp = cli.disable_app(self.app_id)
            resp.assert_no_error()
        return self

    def scale(self, **kwargs):
        """Scales the app according to the provided values. All specified values
        of `memory`, `disk`, or `num_instances` will be updated. If no values
        are specified, then the autoscaling algorithm will be used to scale the
        app. Note that the app _will_ be restarted if `memory` or `disk` change.

        Keyword Args:
            memory (int): Units are MB
            disk (int): Units are MB
            num_instances (int)
        """
        return client.get_autoscaler().scale_app(self.app_id, **kwargs).result

    def _assert_app_id(self):
        if not self.app_id:
            raise Exception("Can't save app without an app_id.")

    @classmethod
    def find_by_id(cls, app_id, **kwargs):
        """Looks up the app object from the "apps" table in the database.
        Does _not_ load from Cloud Foundry.

        Args:
            app_id (str)

        Returns:
            App
        """
        app = client.get_autoscaler().get_app(app_id, **kwargs).result
        return App(app)

    @classmethod
    def list_my_apps(cls):
        """Lists all apps imported into the database.

        Returns:
            App
        """
        apps = client.get_autoscaler().get_apps().result
        return _wrap(apps, cls)

    @classmethod
    def list_available_apps(cls):
        """Lists all apps in the current org / space that are _not_ imported
        into the database.

        Returns:
            App
        """
        apps = client.get_autoscaler().get_available_apps().result
        return _wrap(apps, cls)


class AppStats(Model):
    """This class models the `app_stats` table in the database as well as
    a Cloud Foundry API App instance stat object.
    """

    app_id = None
    time_added = None
    time = None
    cpu = None
    mem = None
    mem_max = None
    disk = None
    disk_max = None
    num_instances = None

    def mem_factor(self):
        """Calculates the ratio of mem to mem_max.

        Returns:
            float: between 0 and 1
        """
        return float(self.mem) / float(self.mem_max)

    @staticmethod
    def get_history(app_id, **kwargs):
        stats = client.get_autoscaler()\
            .get_app_stats_history(app_id, **kwargs).result
        return _wrap(stats, AppStats)
