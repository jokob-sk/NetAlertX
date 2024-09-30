function presenceOverTime(
    timeStamp, 
    onlineCount, 
    offlineCount, 
    archivedCount,
    downCount
  ) {
        var xValues = timeStamp;

        // Data object for online status
        onlineData = {
          label: 'Online',
          data: onlineCount,
          borderColor: "#00000",
          fill: true,
          backgroundColor: "rgba(0, 166, 89, .6)",
          pointStyle: 'circle',
          pointRadius: 3,
          pointHoverRadius: 3
        };

        // Data object for down status
        downData = {          
          label: 'Down',
          data: downCount,
          borderColor: "#00000",
          fill: true,
          backgroundColor: "#dd4b39",          
        };

        // Data object for offline status
        offlineData = {          
          label: 'Offline',
          data: offlineCount,
          borderColor: "#00000",
          fill: true,
          backgroundColor: "#b2b6be",          
        };

        // Data object for archived status
        archivedData = {
          label: 'Archived',
          data: archivedCount,
          borderColor: "#00000",
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
          datasets.push(onlineData); 
        }

        // Check if 'down' status should be displayed
        if(showStats.includes("down"))
        {
          datasets.push(downData); 
        }

        // Check if 'offline' status should be displayed
        if(showStats.includes("offline"))
        {
          datasets.push(offlineData); 
        }

        // Check if 'archived' status should be displayed
        if(showStats.includes("archived"))
        {
          datasets.push(archivedData); 
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
