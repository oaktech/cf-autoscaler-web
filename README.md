# HSDP Cloud Foundry Autoscaler Web UI

This web UI provides a monitoring and management interface for all apps a single Cloud Foundry space.


# Deployment in Cloud Foundry

- Switch to the space where you want to deploy the Web UI using `cf target -o <org> -s <space>`.
- Create a new deployment manifest file based on `manifest.yml`.
  - You will need to set each of these environment variables under the `env:` attribute of your manifest.
    - `CFAS_ORG_NAME`: This is the name of the Organization where the Autoscaler Web is expected to be deployed.
    - `CFAS_SPACE_NAME`: This is the name of the Space where the Autoscaler Web is expected to be deployed.
    - `CFAS_API_URL`: This is the base URL for the Autoscaler API instance in your deployment that will support this Web UI.
    - `CFAS_TOKEN`: This is the Autoscaler API token that you receive when you register this space with the Autoscaler API.
    - `CFAS_SECRET`: This is the Autoscaler API secret that you receive when you register this space with the Autoscaler API.
    - `CFAS_VALIDATE_SSL`: This is an optional parameter, but you may need it if your Autoscaler API has self-signed SSL certs. Valid values are `true` or `false`.
  - To get `CFAS_API_URL` you should ask your Operations team for the URL to your Autoscaler API in your Cloud Foundry deployment. _Remember that there is only one Autoscaler API deployed per Cloud Foundry deployment_.
  The format should be `scheme://autoscaler-api-domain` (no path should be included in this URL).
  - Once you have the Autoscaler API URL, you can register your space for a Web UI.
    - To register, you must sign in at the local Autoscaler API (you will find the registration form at `<CFAS_API_URL>/spaces/manage`).
    _You must sign in with your Cloud Foundry credentials (these are the same credentials you use with `cf login`)._
    - You will be shown a list of registered spaces, and a form for registering any unregistered spaces.
    _You will only be shown spaces that you have access to._
    - Select the space you want to register, and click "Register".
    - Once space registration is finished, you will see a token/secret pair displayed. _These are the `CFAS_TOKEN` and `CFAS_SECRET`, respectively._
      - **Copy these immediately!**
      - **If you refresh the page without saving these credentials, you will need to unregister the space and re-register the space,
      because the token is not saved in the Autoscaler API. Re-registering will not destroy any data that the Autoscaler API has been saving on behalf of the space.
      After you have re-registered, your data will be just as you left it before you re-registered.**
      - **This token/secret pair is only valid for this space. You may not use them to deploy another Autoscaler Web UI to another space.**
- Run `cf push -f <your_manifest_file>`.


# Granting Access to Cloud Foundry Users

Note that in order for any Cloud Foundry users to access your autoscaler Web UI,
they _**must** possess a space role in the same space as the Web UI_ to which they need access.
The minimum required space role is `SpaceAuditor`.


# Configuration

These are environment variables to be used for configuring the Autoscaler Web UI.

| Name | Type | Default | Required? | Description |
| ---- | ---- | ---- | ---- | ---- |
| `CFAS_ORG_NAME` | `str` | | Yes | This is the name of the Organization where the Autoscaler Web is expected to be deployed. _If the Org and Space names do not match where the Web UI is actually deployed, it will not start._ The purpose of this is to prevent the Web UI from accidentally running in a space where it should not be deployed.
| `CFAS_SPACE_NAME` | `str` | | Yes | This is the name of the Space where the Autoscaler Web is expected to be deployed.  _If the Org and Space names do not match where the Web UI is actually deployed, it will not start._ The purpose of this is to prevent the Web UI from accidentally running in a space where it should not be deployed.
| `CFAS_API_URL` | `str` | | Yes | This is the base URL for the Autoscaler API instance in your deployment that will support this Web UI. The format should be `scheme://autoscaler-api-domain` (no path should be included in this URL).
| `CFAS_TOKEN` | `str` |  | Yes | This is the Autoscaler API token that you received when you registered this space with the Autoscaler API.
| `CFAS_SECRET` | `str` | | Yes | This is the Autoscaler API secret that you received when you registered this space with the Autoscaler API.
| `CFAS_VALIDATE_SSL` | `bool` | `true` | No | This indicates whether to validate SSL certs when making HTTPS requests to the Autoscaler API.
| `CFAS_SCALING_MONITOR_INTERVAL` | `int` | `5` | No | Specifies (in seconds) how often the autoscaler worker will collect stats about registered applications.
| `CFAS_SCALING_MIN_INSTANCES` | `int` | `1` | No | Specifies the global, absolute _minimum_ number of CF instances that the autoscaler monitoring user interface will offer to scale down to. This is the lowest value allowed in "Min. Number of Instances" in the "Auto Scaling Parameters" box on the app monitoring page.
| `CFAS_SCALING_MAX_INSTANCES` | `int` | `50` | No | Specifies the global, absolute _maximum_ number of CF instances that the autoscaler monitoring user interface will offer to scale up to. This is the highest value allowed in "Max. Number of Instances" in the "Auto Scaling Parameters" box on the app monitoring page.

# Autoscaling Workflow

This is a brief description of how to use the autoscaler.

## Sign in

Sign in at the user interface (`/signin`) with your Cloud Foundry username and password
(same username and password as you use for `cf login`). This will redirect you to
the Autoscaler API to sign in. On successful sign in, the API will redirect you
back to the Web UI home page.

## Import Apps for Autoscaling

If you're not monitoring any apps, you will be redirected to
"Available Apps" (`/apps/available`) to "Import" any apps you want to monitor for
autoscaling.

## Enable Apps for Autoscaling

By default, when an app is imported, autoscaling is disabled. You can enable
autoscaling in one of two ways. 1) by going to the home page (`/`), finding the
app, and selecting "Enable" OR 2) by viewing the app directly (`/apps/<app_id>`)
and selecting the "Enable autoscaling" button beneath the app name.

## Monitor Apps with Autoscaling

Once you've imported and enabled an app for autoscaling, you can watch it's
performance on the `/apps/<app_id>` page. The app page provides charts and a
form for modifying autoscaling parameters as well as managing the app's scale manually.

### Charts

- The "Num Instances" chart shows the number of Cloud Foundry instances running
your app. This chart is good for watching scaling activity as well.
- The "CPU & Memory Usage" chart shows the app's average CPU and Memory usage of
your app across all instances.
- The "Average CPU Usage" and "Average Memory Usage" gauges are a quick view of
how your app is performing.

- The "Instance CPU, Memory, and Disk Usage" chart is good for seeing how the instances running your
app are performing.

### Scaling Parameters

- The "Auto Scaling Parameters" offers
controls for how the autoscaler makes scaling decisions. The Memory/CPU Low/High
parameters are upper and lower bounds of Memory/CPU, respectively, which the
autoscaler will use to decide when to scale up or down. The Min/Max Number of Instances
are used to set the min/max number of instances that the autoscaler will scale to.
- The "Manual Scaling Parameters" offers
controls to manually scale the app if you want to disable autoscaling.

## App Performance History

This page provides a detailed history of app performance spanning the past 7 days.

- The entire width of the chart represents the amount of time shown in the
"Show History for the past" menu.
- The axes of the chart may be selected as combinations of Num. Instances,
Memory, and CPU using the "Chart Layout" menu.
- The number of points on the chart (the resolution) may be adjusted using
the "Chart resolution" menu. High resolution means more data points. Low resolution means less data points.
- There are two charts shown. A large chart near the top of the page, and
a smaller chart below it. Using the cursor to select a region on the smaller
chart will cause the larger chart to zoom in on the selected region. Note
that it may take a few seconds for the chart to zoom in.

## Autoscaling Tuning Hints

### Autoscaling Strategy

Java based apps will benefit most from the **CPU Based Autoscaling**.
Other apps will probably fine with the **Threshold Based Autoscaling**.

### CPU Low / High

For scaling up, 70-90 % CPU usage is a good level to start scaling up the number of instances.
For scaling down, 50-70 % CPU usage is a good level to start scaling down the number of instances.

### Memory Low / High

For scaling up, 70-85 % Memory usage is a good level to start scaling up the number of instances.
For scaling down, 50-65 % Memory usage is a good level to start scaling down the number of instances.

### Number of Instances Min / Max

In the interest of maintaining high availability, 2 instances is a good minimum to scale down to.
For scaling up, if your app is rather high in Memory/Disk usage, you may want to set the max number of instances
lower in the interest of not using too much Memory/Disk in your Organization.
If your app is light and small in Memory/Disk usage, you can set this value higher to allow
more room for autoscaling to optimize the number of instances to sustain the current load on your application.

# License

GNU GENERAL PUBLIC LICENSE V2
