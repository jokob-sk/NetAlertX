function pia_draw_graph_online_history(pia_js_graph_online_history_time, pia_js_graph_online_history_ondev, pia_js_graph_online_history_dodev, pia_js_graph_online_history_ardev) {
        var xValues = pia_js_graph_online_history_time;

        // alert("dev presence")

        // Data object for online status
        onlineData = {
          label: 'Online',
          data: pia_js_graph_online_history_ondev,
          borderColor: "rgba(0, 166, 89)",
          fill: true,
          backgroundColor: "rgba(0, 166, 89, .6)",
          pointStyle: 'circle',
          pointRadius: 3,
          pointHoverRadius: 3
        };

        // Data object for offline status
        offlineData = {          
          label: 'Offline/Down',
          data: pia_js_graph_online_history_dodev,
          borderColor: "rgba(222, 74, 56)",
          fill: true,
          backgroundColor: "rgba(222, 74, 56, .6)",          
        };

        // Data object for archived status
        archivedData = {
          label: 'Archived',
          data: pia_js_graph_online_history_ardev,
          borderColor: "rgba(220,220,220)",
          fill: true,
          backgroundColor: "rgba(220,220,220, .6)",
        };

        // Array to store datasets
        datasets = [];

        // Get UI presence settings
        showStats = getSetting("UI_PRESENCE");

        // Check if 'online' status should be displayed
        if(showStats.includes("online"))
        {
          datasets.push(onlineData); // Add onlineData to datasets array
        }

        // Check if 'offline' status should be displayed
        if(showStats.includes("offline"))
        {
          datasets.push(offlineData); // Add offlineData to datasets array
        }

        // Check if 'archived' status should be displayed
        if(showStats.includes("archived"))
        {
          datasets.push(archivedData); // Add archivedData to datasets array
        }



        new Chart("OnlineChart", {
          type: "bar",
          scaleIntegersOnly: true,
          data: {
            labels: xValues,
            datasets: datasets
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
            },
            tooltips: {
                mode: 'index'
            }
          }
        });
}
