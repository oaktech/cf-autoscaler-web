;(function() {
  "use strict";
  $(function() {

    var $table = $('#apps');
    var enableDisableApp = createEnableDisableApp(getAppId);
    $table.find('.enable-app, .disable-app')
      .click(toggleTextClick('Disable', 'Enable', enableDisableApp));
    $table.find('.remove-app').click(removeApp);
    $table.find('.import-app').click(importApp);

    function importApp(e) {
      var $this = $(this);
      var appId = getAppId.call(this);
      var opts = {
        method: 'POST',
        url: buildPath('api/apps', appId)
      };

      request(opts, function(err) {
        if (err) {
          console.error(err);
        }

        $this
          .unbind('click')
          .removeClass('btn-success')
          .addClass('btn-info')
          .text('View')
          .attr('href', buildPath('apps', appId));
      });
    }

    function removeApp() {
      var $this = $(this);
      var opts = {
        method: 'DELETE',
        url: buildPath('api/apps', getAppId.call(this))
      };

      $this.closest('tr').remove();
      request(opts, function(err) {
        if (err) {
          console.error(err);
        }
      });
    }

    function getAppId() {
      return $(this).closest('tr').attr('data-app-id');
    }

  });
})();