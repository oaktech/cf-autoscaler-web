;(function() {
  $(function() {
    var maxLines = 1000;
    var $errors = $('#errors');
    var socket = connectSocketIO('/errors');
    socket.on('error', function(err) {
      try {
        var lines = $errors.text().split(/\n/g).concat(formatError(JSON.parse(err)).split(/\n/g));
            if (lines.length > maxLines) {
            lines.splice(maxLines)
        }
        $errors.text(lines.join('\n'));

      } catch (e) {
        console.error(e);
      }
    });

    function formatError(error) {
      return ('[ ' + new Date(error.time * 1000).toString() + ' -- ' + error.type.toUpperCase() + ' ]: ' + (error.message || '???'));
    }
  });
})();