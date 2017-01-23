(function () {
  Chart.plugins.register({
    afterDatasetsDraw: function(chartInstance, easing) {
      // To only draw at the end of animation, check for easing === 1
      var ctx = chartInstance.chart.ctx;
      chartInstance.data.datasets.forEach(function (dataset, i) {
        var meta = chartInstance.getDatasetMeta(i);
        var total = dataset.data.reduce(function(a,b) {return a + b});
        if (!meta.hidden) {
          meta.data.forEach(function(element, index) {
            // Draw the text with the specified font
            ctx.fillStyle = 'rgb(255, 255, 255)';
            var fontSize = 16;
            var fontStyle = 'normal';
            var fontFamily = 'open sans';
            var fontColor = 'white';
            ctx.font = Chart.helpers.fontString(fontSize, fontStyle, fontFamily, fontColor);
            // Just naively convert to string for now
            var percentage = Math.round(dataset.data[index]/total*100) + '%';
            // Make sure alignment settings are correct
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            var padding = 5;
            var position = element.tooltipPosition();
            ctx.fillText(percentage, position.x, position.y - (fontSize / 2) - padding);
          });
        }
      });
    }
  });

  var q1PieData = {
    labels: [
      "No abuse",
      "Substance abuse"
    ],
    datasets: [
      {
        data: [64, 36],
        backgroundColor: [
          "#b8103b",
          "#328ec9"
        ],
        hoverBackgroundColor: [
          "#b8103b",
          "#328ec9"
        ]
      }]
  };
  var q1PieCtx = $("#q1Pie").get(0).getContext("2d");
  var q1Pie = new Chart(q1PieCtx,{
    type: 'pie',
    data: q1PieData
  });
})();
