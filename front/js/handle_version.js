function handleVersion(){

    release_timestamp = getCookie("release_timestamp")

    if(release_timestamp != "")
    {

      build_timestamp = parseInt($('#version').attr("data-build-time").match(  /\d+/g ).join(''))

      // if the release_timestamp is older by 10 min or more as the build timestamp then there is a new release available 
      if(release_timestamp > build_timestamp + 600 )
      {
        console.log("New release!")
        $('#version').attr("class", $('#version').attr("class").replace("myhidden", ""))
        $('#new-version-text').attr("class", $('#new-version-text').attr("class").replace("myhidden", ""))
        
      }
      else{
        console.log("All up-to-date!")        
        $('#current-version-text').attr("class", $('#current-version-text').attr("class").replace("myhidden", ""))        
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
      // get parameter value
      $.get('https://api.github.com/repos/jokob-sk/Pi.Alert/releases', function(data) {
        
        var releases = data;

        if(releases.length > 0)
        {
          release_datetime = releases[0].published_at;
          release_timestamp = new Date(release_datetime).getTime() / 1000;          

          // cache value
          setCookie("release_timestamp", release_timestamp, 5);

          handleVersion();
        }
      });
    } else
    {
      // cache is available, just call the handler
      handleVersion()
    }
  }


// handle the dispaly of the NEW icon
getVersion()