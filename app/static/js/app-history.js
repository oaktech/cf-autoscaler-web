;(function($) {
  "use strict";
  $(function() {
    var historySelector = '#app-stats-history';
    var $message = $('#global-error-message');
    var $chartLayout = $('#chart-axes');
    var $chartInterval = $('#chart-interval');
    var $chartResolution = $('#chart-resolution');
    var currentSamplingRate = {
      begin_time: getQuery('begin_time'),
      end_time: getQuery('end_time'),
      interval: getQuery('interval', getChartInterval()),
      num_points: getQuery('num_points', getChartResolution()),
      sampling_interval: getQuery('sampling_interval')
    };

    var historyChart;
    var times = [], firstTimes;
    var cpus = [], firstCpus;
    var mems = [], firstMems;
    var numInstances = [], firstNumInstances;

    $('#refresh-chart').click(loadHistory);
    $chartInterval.change(function() {
      resetFirstData();
      loadHistory();
      updateHashValue();
    });
    $chartResolution.change(function() {
      resetFirstData();
      loadHistory();
      updateHashValue();
    });
    $chartLayout.change(function() {
      initHistoryChart.call(this);
      updateHashValue();
    });
    initFromHashValue();
    console.log(buildHashValue());

    function buildHashValue() {
      return [
        getCurrentChartLayout(),
        getChartInterval(),
        getChartResolution()
      ].join('/')
    }

    function updateHashValue() {
      window.location.hash = buildHashValue();
    }

    function initFromHashValue() {
      initHistoryChart();
      var parts = location.hash.slice(1).split('/');
      if (3 == parts.length) {
        setCurrentChartLayout(parts[0]);
        setChartInterval(parts[1]);
        setChartResolution(parts[2]);
      }
      loadHistory();
    }

    function loadHistory() {
      request({
        url: '/api' + window.location.pathname + '?' + buildQueryString(getSamplingRates())
      }, function(err, resp, body) {
        if (err) {
          console.log(body.error || err);
          setStatusError.call($message, body.error || err.message);
        }

        if (!body.result) {
          return;
        }

        var results = body.result;

        times = [];
        cpus = [];
        mems = [];
        numInstances = [];

        for (var i in results) {
          var result = results[i];
          times.push(result.time_added);
          cpus.push(result.cpu_percent);
          mems.push(result.mem_percent);
          numInstances.push(result.num_instances);
        }

        if (!firstTimes) {
          firstTimes = times;
        }
        if (!firstCpus) {
          firstCpus = cpus;
        }
        if (!firstMems) {
          firstMems = mems;
        }
        if (!firstNumInstances) {
          firstNumInstances = numInstances;
        }

        historyChart.load({
          axes: buildAxes(),
          columns: buildColumns()
        });
      });
    }

    function initHistoryChart() {
      historyChart = generateLineChart({
        bindto: historySelector,
        subchart: {
          show: true,
          onbrush: createIntervalChange('onbrush')
        },
        size: {
          height: 640
        },
        data: {
          columns: buildColumns(),
          axes: buildAxes(),
          selection: {
            draggable: true,
          }
        },
        axis: buildAxis()
      });

      function createIntervalChange(eventType) {
        var lastChangeTimeout;
        return function onIntervalChange(domain) {
          clearTimeout(lastChangeTimeout);
          lastChangeTimeout = setTimeout(function() {
            console.log('firing ' + eventType);
            console.log(domain);
            currentSamplingRate.begin_time = parseInt(domain[0].getTime() / 1000);
            currentSamplingRate.end_time = parseInt(domain[1].getTime() / 1000);
            loadHistory();
            clearTimeout(lastChangeTimeout);
          }, 1000);
        }
      }
    }

    function buildAxis() {
      var PERCENT_CPU = '% CPU Usage';
      var PERCENT_MEM = '% Memory Usage';
      var PERCENT_MEM_CPU = '% CPU & Memory Usage';

      var type = getCurrentChartLayout();
      var instancesAxis = {
        label: 'Num Instances'
      };

      var axis = {
        x: {
          type: 'timeseries',
          label: 'Time',
          tick: {
            format: '%Y-%m-%d %H:%M:%S',
            rotate: 45,
            multiline: false
          }
        },
        y: instancesAxis,
        y2: undefined
      };

      if ('cpu,mem' == type) {
        axis.y = percentAxis(PERCENT_CPU);
        axis.y2 = percentAxis(PERCENT_MEM);

      } else if ('num_instances,cpu' == type) {
        axis.y2 = percentAxis(PERCENT_CPU);

      } else if ('num_instances,mem' == type) {
        axis.y2 = percentAxis(PERCENT_MEM);

      } else {
        axis.y2 = percentAxis(PERCENT_MEM_CPU);
      }

      return axis;

      function percentAxis(label) {
        return {
          label: label,
          show: true,
          tick: {
            format: formatChartPercent
          }
        }
      }
    }

    function buildAxes() {
      var type = getCurrentChartLayout();
      var axes = {
        num_instances: 'y',
        cpu: 'y2',
        mem: 'y2'
      };

      if ('cpu,mem' == type) {
        axes.cpu = 'y';
      }

      return axes;
    }

    function buildColumns() {
      if (firstTimes && firstTimes !== times && times.length > 1) {
        var beginIndex;
        var endIndex;
        for (var i in firstTimes) {
          if (firstTimes[i] > times[0] && _.isUndefined(beginIndex)) {
            beginIndex = i;
          } else if (firstTimes[i] > times[times.length - 1] && _.isUndefined(endIndex)) {
            endIndex = i;
          }
        }

        if (_.isUndefined(beginIndex)) {
           beginIndex = 0;
        }
        if (_.isUndefined(endIndex)) {
          endIndex = firstTimes.length;
        }

        times = spliceArray(firstTimes, times, beginIndex, endIndex);
        cpus = spliceArray(firstCpus, cpus, beginIndex, endIndex);
        mems = spliceArray(firstMems, mems, beginIndex, endIndex);
        numInstances = spliceArray(firstNumInstances, numInstances, beginIndex, endIndex);
      }


      var columns = [
        ['x'].concat(times),
        ['num_instances'].concat(numInstances),
        ['cpu'].concat(cpus),
        ['mem'].concat(mems)
      ];
      var type = getCurrentChartLayout();
      if ('cpu,mem' == type) {
        columns.splice(1, 1);
      } else if ('num_instances,cpu' == type) {
        columns.splice(3, 1)
      } else if ('num_instances,mem' == type) {
        columns.splice(2, 1)
      }
      return columns;

      function spliceArray(firstArr, arr, begin, end) {
        arr = [begin, end - begin].concat(arr);
        var newArr = [].concat(firstArr);
        Array.prototype.splice.apply(newArr, arr);
        return newArr;
      }
    }

    function resetFirstData() {
      delete currentSamplingRate.begin_time;
      delete currentSamplingRate.end_time;
      firstTimes = undefined;
      firstCpus = undefined;
      firstMems = undefined;
      firstNumInstances = undefined;
    }

    function getSamplingRates() {
      currentSamplingRate.interval = getChartInterval();
      currentSamplingRate.num_points = getChartResolution();
      var copy = _.merge({}, currentSamplingRate);
      if (copy.end_time && copy.begin_time) {
        delete copy.interval;
      }
      return copy;
    }

    function getCurrentChartLayout() {
      return $chartLayout.find('option:selected').val();
    }

    function setCurrentChartLayout(layoutVal) {
      $chartLayout.val(layoutVal);
    }

    function getChartResolution() {
      return parseInt($chartResolution.find('option:selected').val());
    }

    function setChartResolution(resVal) {
      $chartResolution.val(resVal);
    }

    function getChartInterval() {
      return parseInt($chartInterval.find('option:selected').val());
    }

    function setChartInterval(iVal) {
      $chartInterval.val(iVal);
    }
  });
})(jQuery);