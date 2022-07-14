function pia_draw_graph_online_history(pia_js_graph_online_history_time, pia_js_graph_online_history_ondev, pia_js_graph_online_history_dodev) {
        var xValues = pia_js_graph_online_history_time;
        new Chart("OnlineChart", {
          type: "bar",
          data: {
            labels: xValues,
            datasets: [{
              label: 'Online Devices',
              data: pia_js_graph_online_history_ondev,
              borderColor: "#00a65a",
              fill: true,
              backgroundColor: "rgba(0, 166, 89, .6)",
              pointStyle: 'circle',
              pointRadius: 3,
              pointHoverRadius: 3
            }, {
              label: 'Offline/Down Devices',
              data: pia_js_graph_online_history_dodev,
              borderColor: "#dd4b39",
              fill: true,
              backgroundColor: "rgba(222, 74, 56, .6)",
              pointStyle: 'circle',
              pointRadius: 3,
              pointHoverRadius: 3
            }]
          },
          options: {
            legend: {
                display: true,
                labels: {
                    fontColor: "#A0A0A0",
                }
            },
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero:true,
                        fontColor: '#A0A0A0'
                    },
                    gridLines: {
                        color: "rgba(0, 0, 0, 0)",
                    },
                    stacked: true,
                }],
                xAxes: [{
                    ticks: {
                        fontColor: '#A0A0A0',
                    },
                    gridLines: {
                        color: "rgba(0, 0, 0, 0)",
                    },
                    stacked: true,
                }],
            }
          }
        });
}