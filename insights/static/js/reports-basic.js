(function () {
  function drawQ1Pie() {
    var q1PieData = {
      labels: [
        "No abuse",
        "Substance abuse"
      ],
      datasets: [
        {
          data: [128, 72],
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
    drawPie(q1PieData, '#q1Pie', '#q1PieLegend')
  }

  function drawPie(pieData, pieId, legendId) {
    var pieCtx = $(pieId).get(0).getContext("2d");
    var pieLegend = $(legendId);
    var pie = new Chart(pieCtx,{
      type: 'pie',
      data: pieData,
      options: {
        legend: false,
        tooltips: {
          enabled: false
        }
      }
    });
    pieLegend.html(q1Pie.generateLegend());
  }

  $(document).ready(function() {
    drawQ1Pie();
  })
})();
