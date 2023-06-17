function handleVersion(){

    release_timestamp = getCookie("release_timestamp")

    if(release_timestamp != "")
    {

      build_timestamp = parseInt($('#version').attr("data-build-time").match(  /\d+/g ).join(''))

      // if the release_timestamp is older by 10 min or more as the build timestamp then there is a new release available 
      if(release_timestamp > build_timestamp + 600 )
      {
        console.log("New release!")
        // handling the navigation menu icon
        $('#version').attr("class", $('#version').attr("class").replace("myhidden", ""))

        maintenanceDiv = $('#new-version-text')
      }
      else{
        console.log("All up-to-date!")    

        maintenanceDiv = $('#current-version-text')  
      }

      // handling the maintenance section message      
      if(emptyArr.includes(maintenanceDiv) == false && $(maintenanceDiv).length != 0)
      { 
        $(maintenanceDiv).attr("class", $(maintenanceDiv).attr("class").replace("myhidden", ""))
      }
    } 

  }  

  //--------------------------------------------------------------

  function getVersion()
  {
    release_timestamp = getCookie("release_timestamp")    

    // no cached value available
    if(release_timestamp == "")
    {
      $.get('https://api.github.com/repos/jokob-sk/Pi.Alert/releases').done(function(response) {
        // Handle successful response
        var releases = data;

        console.log(releases)

        if(releases.length > 0)
        {
          
          release_datetime = releases[0].published_at;
          release_timestamp = new Date(release_datetime).getTime() / 1000;          

          // cache value
          setCookie("release_timestamp", release_timestamp, 30);

          handleVersion();
        }
        
      }).fail(function(jqXHR, textStatus, errorThrown) {        
       
        $('.version').append(`<p>Github API: ${errorThrown} (${jqXHR.status}), ${jqXHR.responseJSON.message}</p>`)          

      });
    } else
    {
      // cache is available, just call the handler
      handleVersion()
    }
  }


// handle the dispaly of the NEW icon
getVersion()