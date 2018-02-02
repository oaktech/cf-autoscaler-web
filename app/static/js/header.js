;(function() {
  "use strict";
  
  window.request = function(opts, callback) {
    var url = window.buildQueryString(opts.qs, opts.url);
    $.ajax({
      url: url,
      method: (opts.method || 'GET').toUpperCase(),
      headers: opts.headers || {},
      contentType: opts.contentType || undefined,
      data: opts.body,
      dataType: 'json',
      success: function(data, status, xhr) {
        callback(null, xhr, data);
      },
      error: function(xhr, status, err) {
        var data = undefined;
        if (xhr.responseText) {
          var ct = xhr.getResponseHeader('Content-Type');
          if (!_.isUndefined(ct) && !/^application\/json/.test(ct)) {
            data = xhr.responseText;

          } else {
            try {
              data = JSON.parse(xhr.responseText);
            } catch(e) {
              data = xhr.responseText;
            }
          }
        }
        callback(err, xhr, data)
      }
    });
  };

  window.buildQueryString = function(params, url) {
    if (!params) {
      if (url) {
        return url;
      }
      return '';
    }

    var pairs = [];
    for (var name in params) {
      if (params[name]) {
        pairs.push(encodeURIComponent(name) + '=' +
          encodeURIComponent(params[name]));
      }
    }
    pairs = pairs.join('&');

    if (!url) {
      return pairs;
    }

    return url + '?' + pairs;
  };

  window.buildPath = function() {
    var _args = Array.prototype.slice.call(arguments)
      .map(function(arg) {
        return arg.replace(/(?:^\/|\/$)/g, '');
      });
    return '/' + _args.join('/');
  };

  window.$.fn.serializeObject = function() {
      var o = {};
      var a = this.serializeArray();
      $.each(a, function() {
          if (o[this.name] !== undefined) {
              if (!o[this.name].push) {
                  o[this.name] = [o[this.name]];
              }
              o[this.name].push(this.value || '');
          } else {
              o[this.name] = this.value || '';
          }
      });
      return o;
  };

  window.toggleTextClick = function toggleTextClick(text1, text2, action) {
    var rx1 = new RegExp(text1, 'i');
    var rx2 = new RegExp(text2, 'i');
    return function(e) {
      action.call(this, e);
      var $this = $(this);
      var text = $this.text();
      if (rx1.test(text)) {
        $this.text(text2);

      } else if (rx2.test(text)) {
        $this.text(text1);
      }
    }
  };

  window.createEnableDisableApp = function(getAppId) {
    return function enableDisableApp() {
      var $this = $(this);
      var text = $this.text();
      var appId = _.isString(getAppId) ? getAppId : getAppId.call(this);
      var isEnable = /enable/i.test(text);
      var opts = {
        method: 'POST',
        url: buildPath('api/apps', appId, isEnable ? 'enable' : 'disable')
      };
      $this
        .toggleClass('btn-success', isEnable)
        .toggleClass('btn-warning', !isEnable);

      request(opts, function(err) {
        if (err) {
          console.error(err);
        }
      });
    };
  };

  window.padNumber = function padNumber(num, width, char, side) {
    side = side || 'left';
    char = char || '0';

    var pad = '';
    for (var i = 0; i < width - ('' + num).length; i++) {
      pad += char;
    }
    switch (side) {
      case 'right':
        num = '' + num + pad;
        break;
      case 'left':
      default:
        num = pad + num;
    }
    return num;
  };

  window.escapeHtml = function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };

  window.generateLineChart = function generateLineChart(config) {
    return c3.generate(_.merge({
      padding: {
        right: 60
      },
      data: {
        type: 'line',
        x: 'x',
        columns: [
          ['x'],
        ],
      },
      axis: {
        x: {
          type: 'timeseries',
          tick: {
              format: '%Y-%m-%d %H:%M:%S',
              rotate: 45,
              multiline: false
          },
          // height: 130
        }
      },
      point: {
        show: false
      }
    }, config));
  };

  window.formatChartTimeHMS = function formatTimeHMS(date) {
    return [
      padNumber(date.getHours(), 2),
      padNumber(date.getMinutes(), 2),
      padNumber(date.getSeconds(), 2)
    ].join(':')
  };

  window.formatChartPercent = function formatChartPercent(percent) {
    return parseFloat(percent.toFixed(1)) + ' %';
  };

  var queryParams;
  window.getQuery = function parseQuery(name, def) {
    if (queryParams) {
      return name ? queryParams[name] || def : queryParams;
    }

    queryParams = {};
    var pairs = window.location.search.replace('?', '').split(/&/g);
    pairs.map(function (pair) {
      pair = pair.split('=').map(decodeURIComponent);
      var value = pair[1];
      if (!isNaN(value)) {
        if (/\./.test(value)) {
          value = parseFloat(value);
        } else {
          value = parseInt(value);
        }
      }
      queryParams[pair[0]] = value;
    });

    return name ? queryParams[name] || def : queryParams;
  };

  window.connectSocketIO = function connectSocketIO(relativeUrl) {
    var port = ':4443';
    if (location.port && 80 != location.port && 443 != location.port) {
      port = ':' + location.port;
    }
    var host = document.domain + port;
    return io.connect(location.protocol + '//' + host + relativeUrl);
  };

})();
