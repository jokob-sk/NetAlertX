<?php
  //------------------------------------------------------------------------------
  // check if authenticated
  require_once  $_SERVER['DOCUMENT_ROOT'] . '/php/templates/security.php';
?>

<!-- fullCalendar -->

<link rel="stylesheet" href="lib/fullcalendar/fullcalendar.min.css">
  <link rel="stylesheet" href="lib/fullcalendar/fullcalendar.print.min.css" media="print">
  <script src="lib/moment/moment.js"></script>
  <script src="lib/fullcalendar/fullcalendar.min.js"></script>
  <script src="lib/fullcalendar/locale-all.js"></script>

<!-- fullCalendar Scheduler -->
  <link href="lib/fullcalendar-scheduler/scheduler.min.css" rel="stylesheet">
  <script src="lib/fullcalendar-scheduler/scheduler.min.js"></script>


<!-- Calendar -->
<div id="calendar">
</div>


<script>

  // Force re-render calendar on tab change
  // (bugfix for render error at left panel)
  $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function (nav) {
    if ($(nav.target).attr('href') == '#panPresence') {
      $('#calendar').fullCalendar('rerenderEvents');
    }
  });


  // ---------------------------------------
  // query data
  function loadPresenceData()
  {
     // Define Presence datasource and query data
    $('#calendar').fullCalendar('removeEventSources');
    $('#calendar').fullCalendar('addEventSource',
    { url: 'php/server/events.php?action=getDevicePresence&mac=' + mac});
  }

  // ---------------------------------------
  function initializeCalendar_() {

  
    var calendarEl = document.getElementById('calendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridYear,dayGridMonth,timeGridWeek'
      },
      initialView: 'dayGridYear',
      initialDate: '2023-01-12',
      editable: true,
      selectable: true,
      dayMaxEvents: true, // allow "more" link when too many events
      // businessHours: true,
      // weekends: false,
      events: [
        {
          title: 'All Day Event',
          start: '2023-01-01'
        },
        {
          title: 'Long Event',
          start: '2023-01-07',
          end: '2023-01-10'
        },
        {
          groupId: 999,
          title: 'Repeating Event',
          start: '2023-01-09T16:00:00'
        },
        {
          groupId: 999,
          title: 'Repeating Event',
          start: '2023-01-16T16:00:00'
        },
        {
          title: 'Conference',
          start: '2023-01-11',
          end: '2023-01-13'
        },
        {
          title: 'Meeting',
          start: '2023-01-12T10:30:00',
          end: '2023-01-12T12:30:00'
        },
        {
          title: 'Lunch',
          start: '2023-01-12T12:00:00'
        },
        {
          title: 'Meeting',
          start: '2023-01-12T14:30:00'
        },
        {
          title: 'Happy Hour',
          start: '2023-01-12T17:30:00'
        },
        {
          title: 'Dinner',
          start: '2023-01-12T20:00:00'
        },
        {
          title: 'Birthday Party',
          start: '2023-01-13T07:00:00'
        },
        {
          title: 'Click for Google',
          url: 'http://google.com/',
          start: '2023-01-28'
        }
      ]
    });

    calendar.render();
  

}

// -----------------------------------------------------------------------------
function initializeCalendar() {
  $('#calendar').fullCalendar({
    editable          : false,
    droppable         : false,
    defaultView       : 'agendaMonth',
    schedulerLicenseKey: 'GPL-My-Project-Is-Open-Source',
    height            : 'auto',
    firstDay          : 1,
    allDaySlot        : false,
    slotDuration      : '02:00:00',
    slotLabelInterval : '04:00:00',
    slotLabelFormat   : 'H:mm',
    timeFormat        : 'H:mm', 
    locale            : '<?= lang('Presence_CalHead_lang');?>',
    header: {
      left            : 'prev,next today',
      center          : 'title',
      right           : 'agendaYear,agendaMonth,agendaWeek'
    },

    views: {
      agendaYear: {
        type               : 'agenda',
        duration           : { year: 1 },
        buttonText         : '<?= lang('Presence_CalHead_year');?>',
        columnHeaderFormat : ''
      },

      agendaMonth: {
        type               : 'agenda',
        duration           : { month: 1 },
        buttonText         : '<?= lang('Presence_CalHead_month');?>',
        columnHeaderFormat : 'D'
      },
      agendaWeek: {
        buttonText         : '<?= lang('Presence_CalHead_week');?>',
      },
      agendaDay: {
        type              : 'agenda',
        duration          : { day: 1 },
        buttonText        : '<?= lang('Presence_CalHead_day');?>',
        slotLabelFormat   : 'H',
        slotDuration      : '01:00:00'
      }

      
    },

    viewRender: function(view) {
      if (view.name === 'agendaYear') {
        var listHeader  = $('.fc-day-header')[0];
        var listContent = $('.fc-widget-content')[0];

        for (i=0; i < listHeader.length-2 ; i++) {
          listHeader[i].style.borderColor = 'transparent';
          listContent[i+2].style.borderColor = 'transparent';

          if (listHeader[i].innerHTML != '<span></span>') {
            if (i==0) {
              listHeader[i].style.borderLeftColor = '#808080';
            } else {
              listHeader[i-1].style.borderRightColor = '#808080';
              listContent[i+1].style.borderRightColor = '#808080';
            }
            listHeader[i].style.paddingLeft = '10px';
          }   
        };    
      }
    },
 
    columnHeaderText: function(mom) {
      switch ($('#calendar').fullCalendar('getView').name) {
      case 'agendaYear':
        if (mom.date() == 1) {
          return mom.format('MMM');
        } else {
          return '';
        }
        break;
      case 'agendaMonth':
        return mom.date();
        break;
      case 'agendaWeek':
        return mom.format ('ddd D');
        break;
      default:
        return mom.date();
      }
    },

    eventRender: function (event, element) {
      // $(element).tooltip({container: 'body', placement: 'bottom',  title: event.tooltip});
      element.attr ('title', event.tooltip);  // Alternative tooltip
    },
      
    loading: function( isLoading, view ) {
        if (isLoading) {
          showSpinner()
        } else {          
          hideSpinner()
        }
    }

  })
}

// -----------------------------------------------
// INIT with polling for panel element visibility
// -----------------------------------------------

var presencePageInitialized = false;

function initDevicePresencePage() {
  // Only proceed if the Presence tab is visible
  if (!$('#panPresence:visible').length) {
    return; // Exit early if nothing is visible
  }

  // Ensure initialization only happens once
  if (presencePageInitialized) return;
  presencePageInitialized = true;

  showSpinner();

  initializeCalendar();    
  loadPresenceData();
}

// Recurring check to initialize when visible
function devicePresencePageUpdater() {
  initDevicePresencePage();

  setTimeout(devicePresencePageUpdater, 200);
}

devicePresencePageUpdater();



</script>