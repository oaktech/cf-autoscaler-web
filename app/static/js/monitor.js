;(function() {
  "use strict";
  $(function () {
    var MAX_POINTS = 75;
    var FLOW_DURATION = 500;
    var $body = $('body');
    var appId = $('#usage').attr('data-app-id');
    var windowInFocus = false;

    $(window)
      .blur(function () {
        windowInFocus = false;
      })
      .focus(function() {
        windowInFocus = true;
      });

    // Start Socket IO
    var socket = connectSocketIO('/monitor/stats?app_id=' + appId);

    window.monitorSocket = socket;

    socket.on('history', function(history) {
      var historyIsLoaded = 'data-history';
      var loaded = $body.attr(historyIsLoaded);
      if (loaded) {
        return;
      }
      $body.attr(historyIsLoaded, 'yes');
      var latestStats;
      for (var i in history) {
        latestStats = appendStats(history[i]);
      }

      if (latestStats) {
        renderStats(latestStats);
      }
    });

    socket.on('stats', function(stats) {
      window.MONITOR_LENGTH = times.length;
      var latestStats = appendStats(stats);
      renderStats(latestStats, stats.instance_stats);
    });


    // Initialize C3

    function appendStats(stats) {
      var time = stats.time_added;
      var cpuPercent = parseFloat((stats.cpu * 100).toFixed(1));
      var memPercent = parseFloat((stats.mem / stats.mem_max * 100).toFixed(1));
      var _numInstances = stats.num_instances;

      appendArray(times, time);
      appendArray(cpus, cpuPercent);
      appendArray(mems, memPercent);
      appendArray(numInstances, _numInstances);

      return {
        time: time,
        cpuPercent: cpuPercent,
        memPercent: memPercent,
        numInstances: _numInstances
      };
    }

    function renderStats(latestStats, instanceStats) {
      memCpuChart.load({
        duration: FLOW_DURATION,
        columns: [
          ['x'].concat(times),
          ['cpu'].concat(cpus),
          ['mem'].concat(mems)
        ]
      });

      niChart.load({
        duration: FLOW_DURATION,
        columns: [
          ['x'].concat(times),
          ['num_instances'].concat(numInstances)
        ]
      });

      cpuGauge.load({
        columns: [['CPU', latestStats.cpuPercent]]
      });

      memGauge.load({
        columns: [['Memory', latestStats.memPercent]]
      });

      if (instanceStats) {
        instanceStatsChart.load({
          columns: buildInstanceChartData(instanceStats)
        });
      }
    }

    var times = [];
    var cpus = [];
    var mems = [];
    var numInstances = [];

    var memCpuChart = generateLineChart({
      bindto: '#usage',
      data: {
        columns: [
          ['x'].concat(times),
          ['cpu'].concat(cpus),
          ['mem'].concat(mems),
        ],
        axes: {
          cpu: 'y',
          mem: 'y2'
        }
      },
      transition: {
        duration: FLOW_DURATION
      },
      axis: {
        y2: {
          label: '% Memory',
          show: true,
          tick: {
            format: formatChartPercent
          }
        },
        y: {
          label: '% CPU',
          tick: {
            format: formatChartPercent
          }
        },
        x: {
          label: 'Time',
          tick: {
            format: formatChartTimeHMS
          }
        }
      }
    });

    var niChart = generateLineChart({
      bindto: '#num-instances',
      data: {
        columns: [
          ['x'].concat(times),
          ['num_instances'].concat(numInstances),
        ],
        axes: {
          num_instances: 'y',
        }
      },
      transition: {
        duration: FLOW_DURATION
      },
      axis: {
        x: {
          label: 'Time',
          tick: {
            format: formatChartTimeHMS
          }
        },
        y: {
          label: 'Number of Instances'
        }
      }
    });

    var cpuGauge = generateGauge({
      bindto: '#cpu-gauge',
    });

    var memGauge = generateGauge({
      bindto: '#memory-gauge',
    });

    var instanceStatsChart = generateBarChart({
      bindto: '#instance-stats-chart',
      axis: {
        max: {
          y: 100
        },
        x: {
          label: 'App Instance ID',
          tick: {
            format: function(d) {
              return 'Instance #' + d;
            }
          }
        },
        y: {
          label: 'CPU, Mem, & Disk % Usage',
          tick: {
            format: function(d) {
              return '' + d + ' %';
            }
          }
        }
      }
    });

    function appendArray(arr, datapoint) {
      if (arr.length >= MAX_POINTS) {
        arr.shift();
      }
      arr.push(datapoint);
    }

    function buildInstanceChartData(instanceStats) {
      var istats = _.sortBy(instanceStats, function(stat) {
        return parseInt(stat.order);
      });
      var columns = [
        ['CPU'].concat(new Array(istats.length)),
        ['Disk'].concat(new Array(istats.length)),
        ['Memory'].concat(new Array(istats.length))
      ];
      istats.forEach(function(stat) {
        var cpu = 0;
        var disk = 0;
        var mem = 0;
        if (/^RUNNING/i.test(stat.state)) {
          cpu = Math.round(stat.cpu * 100);
          disk = Math.round(stat.disk / stat.disk_max * 100);
          mem = Math.round(stat.mem / stat.mem_max * 100);
        }
        var order = parseInt(stat.order);
        columns[0][order + 1] = cpu;
        columns[1][order + 1] = disk;
        columns[2][order + 1] = mem;
      });

      return columns;
    }

    function generateGauge(config) {
      return c3.generate(_.merge({
        data: {
          type: 'gauge',
          columns: []
        },
        gauge: {
          title: 'test',
          label: {
            format: function(value, ratio) {
              return value + ' %';
            },
            show: false // to turn off the min/max labels.
          },
          min: 0, // 0 is default, //can handle negative min e.g. vacuum / voltage / current flow / rate of change
          max: 100, // 100 is default
          units: ' %',
          width: 39 // for adjusting arc thickness
        },
        color: {
            pattern: ['#60B044', '#F6C600', '#F97600', '#FF0000'],
            threshold: {
                values: [40, 60, 80, 100]
            }
        },
        size: {
            height: 200
        }
      }, config));
    }

    function generateBarChart(config) {
      return c3.generate(_.merge({
        data: {
          columns: [],
          type: 'bar'
        },
        bar: {
          width: {
            ratio: 0.5 // this makes bar width 50% of length between tickss
          }
        }
      }, config));
    }

  });

})();
