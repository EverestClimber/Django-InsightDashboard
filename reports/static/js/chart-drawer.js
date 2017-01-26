(function() {

  window.ChartDrawer = {
    drawPie: drawPie,
    drawHorizontalBarChart: drawHorizontalBarChart,
    drawVerticalBarChart: drawVerticalBarChart
  };

  function drawPie(pieData, pieId, legendId) {
    var $pieCtx = $(pieId).get(0).getContext("2d");
    var $pieLegend = $(legendId);
    var pie = new Chart($pieCtx,{
      type: 'pie',
      data: pieData,
      options: {
        legend: false,
        tooltips: {
          enabled: false
        }
      }
    });
    $pieLegend.html(pie.generateLegend());
    _filterLegend();

    function _filterLegend() {
      var $lis = $pieLegend.find('ul > li');

      $lis.each(function(index, li) {
        if (pieData.datasets[0].data[index] == 0) {
          $(li).empty();
        }
      });

      if (pieData.hideLastLegendItem) {
        $lis.last().empty();
      }
    }
  }

  function drawHorizontalBarChart(chartId, chartData) {
    var $horizontalBarChart = $(chartId);

    drawYLabels($horizontalBarChart, chartData);
    drawBars($horizontalBarChart, chartData);
    adjustXLabels($horizontalBarChart, chartData);
    initTooltips($horizontalBarChart);

    function drawBars($chart, data) {
      var $bars = $chart.find('.horizontal-bars');

      data.forEach(function (item) {
        if (item.positiveNum !== -1 && item.negativeNum !== -1) {
          _drawNonEmptyBar($bars, item);
        } else {
          _drawEmptyBar($bars, item);
        }
      });
    }

    function drawYLabels($chart, data) {
      var $yLabels = $chart.find('.y-labels');

      data.forEach(function (item) {
        var $label = $('<div class="h-chart-y-label">' + item.label + '</div>');
        $yLabels.append($label);
      });
    }

    function adjustXLabels($chart, data) {
      var $xLabels = $chart.find('.x-labels');
      var xLabelsPaddingLeft = $chart.find('.y-labels').outerWidth();

      $xLabels.css('padding-left', xLabelsPaddingLeft);
    }

    function initTooltips($chart) {
      $chart.find('[data-toggle="tooltip"]').tooltip()
    }

    function _drawNonEmptyBar($bars, item) {
      var $bar = $('<div class="bar"></div>');

      var $positivePortionText = $('<span>' + item.positiveNum + '</span>');
      var $negativePortionText = $('<span>' + item.negativeNum + '</span>');

      var $positivePortion = $(
        '<div class="portion blue" ' +
        'data-toggle="tooltip" ' +
        'data-placement="top"' +
        ' title="' + item.positiveNum + '">' +
        '</div>'
      ).html($positivePortionText);

      var $negativePortion = $(
        '<div class="portion red" ' +
        'data-toggle="tooltip" ' +
        'data-placement="top"' +
        ' title="' + item.negativeNum + '">' +
        '</div>'
      ).html($negativePortionText);

      var positiveWidth = _calcPositiveWidth(item);

      var negativeWidth = 100 - positiveWidth;

      $negativePortion.css('width', negativeWidth + '%');
      $positivePortion.css('width', positiveWidth + '%');

      $bar.append($positivePortion);
      $bar.append($negativePortion);
      $bars.append($bar);

      _hideTextIfOverflows($negativePortion, $negativePortionText);
      _hideTextIfOverflows($positivePortion, $positivePortionText);
    }

    function _drawEmptyBar($bars, item) {
      var $bar = $('<div class="bar"></div>');

      var $emptyPortion = $(
        '<div class="portion empty" ' +
        'data-toggle="tooltip" ' +
        'data-placement="top"' +
        ' title="n/a">' +
        '</div>'
      ).html('n/a');

      $bar.append($emptyPortion);
      $bars.append($bar);
    }

    function _hideTextIfOverflows($container, $text) {
      if (!_isEnoughSpaceForText($container, $text)) {
        $container.empty();
      }
    }

    function _isEnoughSpaceForText($container, $text) {
      return $container.outerWidth() > $text.outerWidth();
    }

    function _calcPositiveWidth(item) {
      var MIN_WIDTH = 1;
      var MAX_WIDTH = 99;

      var positiveWidth = item.positiveNum / (item.positiveNum + item.negativeNum) * 100;
      if (positiveWidth > MAX_WIDTH) {
        positiveWidth = MAX_WIDTH;
      } else if (positiveWidth < MIN_WIDTH) {
        positiveWidth = MIN_WIDTH;
      }

      return positiveWidth;
    }
  }

  function drawVerticalBarChart(chartId, labelsId, data) {
    var barChart = new Chartist.Bar(chartId, {
      labels: data.labels,
      series: [data.series]
    }, {
      stackBars: false,
      high: 100,
      low: 0,
      axisY: {
        type: Chartist.FixedScaleAxis,
        ticks: [0, 25, 50, 75, 100],
        labelInterpolationFnc: setYAxisLabels
      },
      axisX: {
        showGrid: false
      }
    })
      .on('draw',setBarPercentage)
      .on('draw', setBarWidth)
      .on('created', drawBarLabels);

    $(document).on('resize', drawBarLabels);

    function setBarWidth(data) {
      if (data.type === "bar") {
        data.element.attr({
          style: 'stroke-width: 22px'
        });
      }
    }

    function setBarPercentage(data) {
      if (data.type === "bar") {
        var barHorizontalCenter, barVerticalCenter, label, value;
        barHorizontalCenter = data.x1 + (data.element.width() * .5);
        barVerticalCenter = data.y1 + (data.element.height() * -1) - 10;
        value = data.element.attr('ct:value');
        label = new Chartist.Svg('text');
        if (value == '-1') {
          label.text('n/a');
        } else {
          label.text(value + '%');
        }
        label.addClass("ct-barlabel");
        label.attr({
          x: barHorizontalCenter,
          y: barVerticalCenter,
          'text-anchor': 'middle'
        });
        return data.group.append(label);
      }
    }

    function setYAxisLabels(value) {
      return value % 50 == 0 ? value + '%' : '';
    }

    function drawBarLabels() {
      var $barChartContainer = $(chartId);
      var barChartContainerPosition = $barChartContainer.offset();
      var $labels = $(labelsId);
      var $bars = $barChartContainer.find('.ct-bar');

      $labels.empty();

      $bars.each(function(i, bar) {
        var $bar = $(bar);
        var barPosition = $bar.offset();
        var $label = $('<div class="ct-bar-label">' + barChart.data.labels[i] + '</div>');
        $labels.append($label);
        var barHeight = bar.getBBox().height;
        var barWidth = bar.getBBox().width;
        var labelTop = barPosition.top - barChartContainerPosition.top + barHeight + 10;
        var labelLeft = barPosition.left - barChartContainerPosition.left + barWidth/2 - $label.width()/2;
        $label.css('top', labelTop);
        $label.css('left', labelLeft);
        $label.css('height', $label.width());
      });
    }
  }

})();
