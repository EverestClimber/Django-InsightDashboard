(function () {
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
  var q1PieCtx = $("#q1Pie").get(0).getContext("2d");
  var q1PieLegend = $('#q1PieLegend');
  var q1Pie = new Chart(q1PieCtx,{
    type: 'pie',
    data: q1PieData,
    options: {
      legend: false,
      tooltips: {
        enabled: false
      }
    }
  });
  q1PieLegend.html(q1Pie.generateLegend());
})();
