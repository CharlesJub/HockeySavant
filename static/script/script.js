jQuery.noConflict();
jQuery(document).ready(function($) {
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
      },
      error: function(error) {
        console.error('Error fetching data: ', error);
      }
    });
  });
  
  function updateTable(data) {
    var table = $('#table tbody');
    table.empty(); // Clear existing data

    data.forEach(function(player) {
      var newRow = '<tr>';
      newRow += '<td><img class="player-head" src="https://assets.nhle.com/mugs/nhl/latest/' + player.id + '.png" loading="eager"><a class="player-link" href="/player/' + player.id + '">' + player.name + '</a></td>';
      newRow += '<td>' + String(player.season).substring(0,4) + '</td>';
      newRow += '</tr>';
      table.append(newRow);
    });
  }
});


