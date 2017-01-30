(function() {
  Chart.plugins.register({
    afterDatasetsDraw: drawPercentage
  });

  Chart.defaults.global.tooltips.custom = function(tooltip) {
    // Tooltip Element
    var tooltipEl = document.getElementById('chartjs-tooltip');
    // Hide if no tooltip
    if (tooltip.opacity === 0) {
      tooltipEl.style.opacity = 0;
      return;
    }
    // Set caret Position
    tooltipEl.classList.remove('above', 'below', 'no-transform');
    if (tooltip.yAlign) {
      tooltipEl.classList.add(tooltip.yAlign);
    } else {
      tooltipEl.classList.add('no-transform');
    }
    function getBody(bodyItem) {
      return bodyItem.lines;
    }
    // Set Text
    if (tooltip.body) {
      var titleLines = tooltip.title || [];
      var bodyLines = tooltip.body.map(getBody);
      var innerHtml = '<thead>';
      titleLines.forEach(function(title) {
        innerHtml += '<tr><th>' + title + '</th></tr>';
      });
      innerHtml += '</thead><tbody>';
      bodyLines.forEach(function(body, i) {
        var colors = tooltip.labelColors[i];
        var style = 'background:' + colors.backgroundColor;
        style += '; border-color:' + colors.borderColor;
        style += '; border-width: 2px';
        var span = '<span class="chartjs-tooltip-key" style="' + style + '"></span>';
        innerHtml += '<tr><td>' + span + body + '</td></tr>';
      });
      innerHtml += '</tbody>';
      var tableRoot = tooltipEl.querySelector('table');
      tableRoot.innerHTML = innerHtml;
    }
    var position = $(this._chart.canvas).offset();
    // Display, position, and set styles for font
    tooltipEl.style.opacity = 1;
    tooltipEl.style.left = position.left + tooltip.caretX + 'px';
    tooltipEl.style.top = position.top + tooltip.caretY + 'px';
    tooltipEl.style.fontSize = tooltip.fontSize;
    tooltipEl.style.fontStyle = tooltip._fontStyle;
    tooltipEl.style.padding = tooltip.yPadding + 'px ' + tooltip.xPadding + 'px';
  };

  function drawPercentage(chartInstance, easing) {
    // To only draw at the end of animation, check for easing === 1
    var ctx = chartInstance.chart.ctx;
    chartInstance.data.datasets.forEach(function (dataset, i) {
      var meta = chartInstance.getDatasetMeta(i);
      var total = dataset.data.reduce(function(a,b) {return a + b});
      if (!meta.hidden) {
        meta.data.forEach(function(element, index) {
          var percentage = dataset.data[index]/total*100;
          if (percentage >= 8) {
            _drawPercentageForSegment(percentage, element, ctx);
          }
        });
      }
    });
  }

  function _drawPercentageForSegment(percentage, element, ctx) {
    //Check for almost white background TODO: change this comparison - too fragile
    if (element._model.backgroundColor == '#f9f9f9') {
      ctx.fillStyle = 'rgb(61, 61, 61)';
    } else {
      ctx.fillStyle = 'rgb(255, 255, 255)';
    }
    var fontSize = 14;
    var fontStyle = 'bold';
    var fontFamily = 'open sans';
    var fontColor = 'white';
    ctx.font = Chart.helpers.fontString(fontSize, fontStyle, fontFamily, fontColor);
    // Just naively convert to string for now
    var percentageStr = Math.round(percentage) + '%';
    // Make sure alignment settings are correct
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    var position = element.tooltipPosition();
    ctx.fillText(percentageStr, position.x, position.y);
  }
})();
