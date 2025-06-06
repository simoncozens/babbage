function createGauge(score, id, opts) {
  Highcharts.chart(id, {
    chart: {
      type: "gauge",
      height: opts.height,
      animation: false,
    },

    title: {
      text: opts.title,
    },

    pane: {
      startAngle: -150,
      endAngle: 150,
      background: {
        backgroundColor: "transparent",
        borderWidth: 0,
      },
    },

    plotOptions: {
      gauge: {
        animation: false,
        pivot: {
          backgroundColor: "transparent",
        },
        dial: {
          backgroundColor: "transparent",
          baseWidth: 0,
        },
      },
    },

    yAxis: {
      min: opts.yAxis.min || 0,
      max: opts.yAxis.max || 100,
      minorTickInterval: 0,
      tickColor: "#ffffff",
      tickLength: 40,
      tickPixelInterval: 40,
      tickWidth: 0,
      lineWidth: 0,
      title: {
        text: opts.yAxis.title,
        style: {
          color: "#000000",
          fontFamily: "NicoPups",
          fontSize: "16px",
        },
      },
      labels: {
        ...opts.labels,
        style: {
          fontSize: "16px",
        },
      },
      plotBands: [
        {
          from: 1,
          to: score,
          color: {
            pattern: {
              image: "https://usetrmnl.com/images/grayscale/gray-2.png",
              width: 12,
              height: 12,
            },
          },
          innerRadius: "82%",
          borderRadius: "50%",
        },
        {
          from: score + 1,
          to: 100,
          color: {
            pattern: {
              image: "https://usetrmnl.com/images/grayscale/gray-5.png",
              width: 12,
              height: 12,
            },
          },
          innerRadius: "82%",
          borderRadius: "50%",
        },
      ],
    },

    series: [
      {
        name: "Score",
        data: [score],
        dataLabels: {
          borderWidth: 0,
          style: {
            fontSize: opts.series.fontSize,
            fontWeight: opts.series.fontWeight || "400",
            fontFamily: opts.series.fontFamily || "inherit",
          },
        },
      },
    ],

    credits: {
      enabled: false,
    },
  });
}

function textRating(score) {
  if (score <= 50) {
    return "Low";
  } else if (score <= 65) {
    return "Pay Attention";
  } else if (score < 80) {
    return "Fair";
  } else {
    return "Good";
  }
}
