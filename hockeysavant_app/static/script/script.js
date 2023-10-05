jQuery.noConflict();
jQuery(document).ready(function($) {
  // Check if game-start exists before running set date
  if ($('.game-start').length) {
    setTime();
  }

  if ($('#player-search').length){
    document.getElementById("player-search").addEventListener("keyup", filterTableSearch);
  }
  if ($('#player-table').length){
    $.ajax({
      url: '/players_data',
      type: 'GET',
      dataType: 'json',
      data: {
        position: $('#position').val(),
        season: $('#season').val(),
        min_played_toi: $('#min-played-toi').val()
      },
      success: function(data) {
        // Handle the data received from the server
        // Update the HTML on the /players page with the data
        updateTable(data);          
      },
      error: function(error) {
        console.error('Error fetching data: ', error);
      }
    });
  }
  
  $('.stats-filter').change(function() {
    // Use AJAX to fetch data from the server
    $.ajax({
      url: '/players_data',
      type: 'GET',
      dataType: 'json',
      data: {
        position: $('#position').val(),
        season: $('#season').val(),
        min_played_toi: $('#min-played-toi').val()
      },
      success: function(data) {
        // Handle the data received from the server
        // Update the HTML on the /players page with the data
        updateTable(data);        
        filterTableSearch;  
      },
      error: function(error) {
        console.error('Error fetching data: ', error);
      }
    });
  });
  
  function updateTable(data) {
    var table = $('#player-table tbody');
    table.empty(); // Clear existing data

    data.forEach(function(player) {
      var newRow = '<tr>';
      newRow += '<td><img class="player-head" src="https://assets.nhle.com/mugs/nhl/latest/' + player.id + '.png" loading="eager"><a class="player-link" href="/player/' + player.id + '">' + player.lastFirstName + '</a></td>';
      newRow += '<td>' + String(player.season).substring(0,4) + '</td>';
      newRow += '</tr>';
      table.append(newRow);
    });
  }
});



function filterTableSearch() {
  const input = this.value.toLowerCase();
  const table = document.getElementById("player-table");
  const rows = table.getElementsByTagName("tbody")[0].getElementsByTagName("tr");
  for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const cells = row.getElementsByTagName("td");
      let found = false;

      for (let j = 0; j < cells.length; j++) {
          const cell = cells[j];
          if (cell.innerText.toLowerCase().indexOf(input) > -1) {
              found = true;
              break;
          }
      }

      if (found) {
          row.style.display = "";
      } else {
          row.style.display = "none";
      }
  }
}




function setTime() {
  const datetimeElements = document.getElementsByClassName("game-start");

  // Convert the NodeList to an array using Array.from()
  const datetimeArray = Array.from(datetimeElements);

  datetimeArray.forEach(function(dateElement) {
    const dateText = dateElement.innerText;
    const dateObject = new Date(dateText);
    const options = { hour: 'numeric', minute: 'numeric', hour12: true };
    const formatedTime = dateObject.toLocaleTimeString(undefined, options);
    // Display the formatted time
    dateElement.innerText = formatedTime;
  });
}