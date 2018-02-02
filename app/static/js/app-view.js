;(function() {
  "use strict";

  $(function () {

    var appId = $('#app-id').val();
    var enableDisableApp = createEnableDisableApp(appId);

    $('[data-toggle="tooltip"]').tooltip({delay: 500, container: 'body'});
    $('#enable-disable-app').click(toggleTextClick('Enable Autoscaling', 'Disable Autoscaling', enableDisableApp));

    var $lastUpdateTime = $('#last-update-time');
    var $scalingConfig;
    var $scaleDisk = $('.scale-disk');
    var $scaleMemory = $('.scale-memory');
    var $scaleInstances = $('.scale-instances');

    setupScalingConfigForm();
    $(document).on('new-scaling-config-form', setupScalingConfigForm);

    $scaleDisk.change(scale('scale_disk', 'Scaling disk will require an app restart. Are you sure?'));
    $scaleMemory.change(scale('scale_memory', 'Scaling memory will require an app restart. Are you sure?'));
    $scaleInstances.change(scale('scale_instances', 'Scaling the number of instances manually may disrupt app traffic. Are you sure?'));

    if (window.monitorSocket) {
      window.monitorSocket.on('stats', function(stats) {
        $lastUpdateTime.text('last update: ' + new Date().toString());
        selectCurrentValue.call($scaleMemory, 'mem_max', stats, 'MB');
        selectCurrentValue.call($scaleDisk, 'disk_max', stats, 'MB');
        selectCurrentValue.call($scaleInstances, 'num_instances', stats);
      });
    }

    function setupScalingConfigForm() {
      $scalingConfig = $('#scaling-config');
      $scalingConfig.submit(function(e) {
        e.preventDefault();
        var $this = $(this);
        request({
          method: 'POST',
          url: buildPath('api/apps', appId, 'save'),
          body: $this.serializeObject(),
        }, statusRequestHandler('#scaling-config-error', 'Updated autoscaling config!'))
      });
    }

    function scale(scaleType, confirmMessage) {
      return function() {
        if (confirmMessage && !confirm(confirmMessage)) {
          return;
        }
        var $this = $(this);
        var body = {};
        body[scaleType] = $this.find('option:selected').val();
        request({
          method: 'POST',
          url: buildPath('api/apps', appId, 'scale'),
          body: body
        }, statusRequestHandler('#manual-scaling-error', 'Updated ' + $this.prev('h3').text() + ' successfully!'));
      }
    }

    function selectCurrentValue(maxValueKey, stats, unit) {
      this.find('option').each(function() {
        var $this = $(this);
        var value = $this.val();
        var valueMax = parseInt(stats[maxValueKey]);
        if ('MB' == unit) {
           valueMax /= (1024 * 1024)
        }

        if (valueMax == value) {
          $this.attr('selected', '')
        } else {
          $this.removeAttr('selected');
        }
      });
    }

  });

})();