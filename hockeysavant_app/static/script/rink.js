
window.onload = function() {
    const canvas = document.getElementById("rink_canvas");
    copyRinkToCanvas(canvas.width, canvas.height);
    copyGoalToCanvas();
};

function copyRinkToCanvas(width, height) {
    var image = document.getElementById("rink_image")
    var canvas = document.querySelector("canvas")

    var ctx = canvas.getContext("2d");

    ctx.drawImage(
        image, 
        0,0,
        width, height

    );
}

function mapValue(value, old_min, old_max, new_min, new_max) {
    // Map the value from the original range to the new range
    // Formula: (value - old_min) / (old_max - old_min) * (new_max - new_min) + new_min
    var mappedValue = (value - old_min) / (old_max - old_min) * (new_max - new_min) + new_min;
    return mappedValue;
}

function updateRink(data) {
    const canvas = document.getElementById("rink_canvas");
    const ctx = canvas.getContext("2d");
    const CIRCLE_RADIUS = 5;

    // Call the clearCanvas function whenever you want to clear the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const newCanvas = canvas.cloneNode(true);
    canvas.parentNode.replaceChild(newCanvas, canvas);
    copyRinkToCanvas(newCanvas.width, newCanvas.height);
    const new_ctx = newCanvas.getContext("2d");
    new_ctx.fillStyle = "green";
    // Set the circle border color and width
    new_ctx.strokeStyle = "black"; // Border color
    new_ctx.lineWidth = 0.5;       // Border width

    // Add a single click event listener to the canvas
    newCanvas.addEventListener("click", function (event) {
        const clickX = event.clientX - newCanvas.getBoundingClientRect().left;
        const clickY = event.clientY - newCanvas.getBoundingClientRect().top;

        data.forEach(dataElement => {
            const x = mapValue(dataElement.coordsX, -100, 100, 0, newCanvas.width);
            const y = mapValue(-dataElement.coordsY, -100, 100, 0, newCanvas.height);
            
            // Calculate the distance between the click point and the center of the circle
            const distance = Math.sqrt(Math.pow(clickX - x, 2) + Math.pow(clickY - y, 2));

            // Check if the click is within the circle
            if (distance <= CIRCLE_RADIUS) { 
                document.location.href = '/video/' + dataElement.gameId + '-' + dataElement.playId;
            }
        });
    });

    const tooltip = document.getElementById("tooltip");

    newCanvas.addEventListener("mousemove", function (event) {
      const clickX = event.clientX - newCanvas.getBoundingClientRect().left;
      const clickY = event.clientY - newCanvas.getBoundingClientRect().top;
      
      
      let hoveredElement = null; // Use a different variable name to avoid confusion
      let tooltipX = null;
      let tooltipY = null;
    
      data.forEach(dataElement => {
          const x = mapValue(dataElement.coordsX, -100, 100, 0, newCanvas.width);
          const y = mapValue(-dataElement.coordsY, -100, 100, 0, newCanvas.height);
          
          // Calculate the distance between the click point and the center of the circle
          const distance = Math.sqrt(Math.pow(clickX - x, 2) + Math.pow(clickY - y, 2));


          // Check if the click is within the circle
          if (distance <= CIRCLE_RADIUS) { 
            hoveredElement = dataElement;
            tooltipX = x;
            tooltipY = y;
          }
      });
      
      if (hoveredElement) {
        newCanvas.style.cursor = "pointer";

        tooltip.style.display = "block";

        tooltip.textContent = hoveredElement.eventDescription;

        const tooltipWidth = tooltip.offsetWidth;
        const tooltipHeight = tooltip.offsetHeight;  
        tooltip.style.left = `${tooltipX - tooltipWidth/2}px`;
        tooltip.style.top = `${tooltipY - tooltipHeight - 6}px`;    
        } else {
          // Change Mouse
          newCanvas.style.cursor = "default";
          // Hide tooltip
          tooltip.style.display = "none";
        }
    });
    const player_id = $('.player_info').attr('id');
    console.log(player_id)
    data.forEach(dataElement => {
        const x = mapValue(dataElement.coordsX, -100, 100, 0, newCanvas.width);
        const y = mapValue(-dataElement.coordsY, -100, 100, 0, newCanvas.height);
        console.log(dataElement)
        
        if (dataElement.eventPlayer1 == player_id) {
            new_ctx.fillStyle = "red";
        } else if (dataElement.eventPlayer2 == player_id | dataElement.eventPlayer3 == player_id) {
            new_ctx.fillStyle = "blue";
        } else {
            new_ctx.fillStyle = "#808080";
        }
            
        // Draw the circle with a border
        new_ctx.beginPath();
        new_ctx.arc(x, y, CIRCLE_RADIUS, 0, Math.PI * 2); // Draw the circle
        new_ctx.fill(); 
        new_ctx.stroke(); // This line adds the border
        new_ctx.closePath(); 
    });
}

function interpolateColor(color1, color2, color3, value) {
    // Ensure the value is within the range [0, 100]
    value = Math.min(100, Math.max(0, value));
  
    // Calculate the interpolation factor based on the value
    const interpolationFactor = value / 50;
  
    // Interpolate between color1 and color2 if value is less than 50
    if (value < 50) {
      const r = Math.round(color1[0] + (color2[0] - color1[0]) * interpolationFactor);
      const g = Math.round(color1[1] + (color2[1] - color1[1]) * interpolationFactor);
      const b = Math.round(color1[2] + (color2[2] - color1[2]) * interpolationFactor);
      return `rgb(${r}, ${g}, ${b})`;
    } else { // Interpolate between color2 and color3 if value is greater than or equal to 50
      const r = Math.round(color2[0] + (color3[0] - color2[0]) * (interpolationFactor - 1));
      const g = Math.round(color2[1] + (color3[1] - color2[1]) * (interpolationFactor - 1));
      const b = Math.round(color2[2] + (color3[2] - color2[2]) * (interpolationFactor - 1));
      return `rgb(${r}, ${g}, ${b})`;
    }
  }


function updatePercentileGraph(data) {
    const percentileValues = document.querySelectorAll('.percentileValue');
    percentileValues.forEach(function (percentileValue){
        const percentile = Math.round(data[0][percentileValue.id]);
        const percentileText = percentileValue.querySelector('#percentile-text');
        const percentile_bar = percentileValue.querySelector('#percentile-bar');
        const percentile_circle = percentileValue.querySelector('#percentile-circle');
        const percentile_head = percentileValue.querySelector('#percentile-head');
        const bar_width = 15 + (percentile * 2.8);
        percentileText.textContent = percentile; 
        percentile_bar.style.width = bar_width + 'px';
        percentile_circle.style.transform = `translate(${105 + bar_width}px, 10px)`
        // rgb(54, 97, 173), rgb(170, 170, 170), rgb(216, 33, 41)
        const low = [54, 97, 173];
        const mid = [170, 170, 170];
        const high = [216, 33, 41];
        const interpolatedColor = interpolateColor(low, mid, high, percentile);
        percentile_bar.style.fill = interpolatedColor;
        percentile_head.style.fill = interpolatedColor;
        
    });
    

}
function copyGoalToCanvas(){
    var canvas = document.querySelector("canvas");
    var goalMarks = document.querySelectorAll("#goal_mark");
    


    var ctx = canvas.getContext("2d");

    // Loop through the goal marks and draw circles on the canvas
    goalMarks.forEach(function (goalMark) {
        var x = parseFloat(goalMark.getAttribute("x")); // Parse x coordinate as a float
        var y = parseFloat(goalMark.getAttribute("y")); // Parse y coordinate as a float
        var gameId = goalMark.getAttribute("game-id"); // Parse x coordinate as a float
        var goalId = goalMark.getAttribute("goal-id"); // Parse y coordinate as a float
        
        // Map the coordinates if needed (e.g., from [-100, 100] to [0, canvas.width/height])
        x = mapValue(x, -100, 100, 0, canvas.width);
        y = mapValue(y, -100, 100, 0, canvas.height);

        // Set the circle fill color
        ctx.fillStyle = "green";

        // Set the circle border color and width
        ctx.strokeStyle = "black"; // Border color
        ctx.lineWidth = 2;       // Border width

        // Draw the circle with a border
        ctx.beginPath();
        ctx.arc(x, y, CIRCLE_RADIUS, 0, Math.PI * 2); // Draw the circle
        ctx.fill();
        ctx.stroke(); // This line adds the border
        ctx.closePath();

        // Add a click event listener to the canvas
        canvas.addEventListener("click", function (event) {
            var clickX = event.clientX - canvas.getBoundingClientRect().left;
            var clickY = event.clientY - canvas.getBoundingClientRect().top;
            
            // Calculate the distance between the click point and the center of the circle
            var distance = Math.sqrt(Math.pow(clickX - x, 2) + Math.pow(clickY - y, 2));
            
            // Check if the click is within the circle
            if (distance <= CIRCLE_RADIUS) {
                document.location.href = '/video/'+gameId+'-'+goalId;
            }
        });
    });
}

// Code for rink updating 
// TODO - add more info to the tool tip
// TODO - add season filter
// TODO - add en filter 
jQuery(document).ready(function($) {
    
    // Percentile Stuff
    
    // Get rink points on load:
    setTimeout(function() {
        const player_id = $('.player_info').attr('id');
        const strength_type = $('.event-filter.active').attr('name');
        const highlight_type = $('.strength-filter.active').attr('name');

        $.ajax({
          url: '/goal_data/' + player_id,
          type: 'GET',
          dataType: 'json',
          data: {
            highlight: highlight_type,
            strength: strength_type
          },
          success: function(data) {
            // Handle the data received from the server
            // Update the HTML on the /players page with the data
            updateRink(data);      
          },
          error: function(error) {
            console.error('Error fetching goal data: ', error);
          }
        });

        $.ajax({
            url: '/skater_percentile/' + player_id,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
            // Handle the data received from the server
            // Update the HTML on the /players page with the data
            updatePercentileGraph(data);
            },
            error: function(error) {
            console.error('Error fetching percentile data: ', error);
            }
        });
    }, 1);
    
    // Reload data with new filters
    $('.btn.video-filter').click(function(){
        // Add small wait to make sure the button clicked is the active button
        setTimeout(function() {
        var strength_type = $('.event-filter.active').attr('name');
        var highlight_type = $('.strength-filter.active').attr('name');
        var player_id = $('.player_info').attr('id');
        $.ajax({
            url: '/goal_data/' + player_id,
            type: 'GET',
            dataType: 'json',
            data: {
            highlight: highlight_type,
            strength: strength_type
            },
            success: function(data) {
            // Handle the data received from the server
            // Update the HTML on the /players page with the data
            updateRink(data);       
            },
            error: function(error) {
            console.error('Error fetching data: ', error);
            }
        });

        }, 1);
    });
});





