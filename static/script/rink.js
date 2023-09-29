window.onload = function() {
    copyRinkToCanvas();
    copyGoalToCanvas();
};

function copyRinkToCanvas(){
    var image = document.getElementById("rink_image")
    var canvas = document.querySelector("canvas")

    var ctx = canvas.getContext("2d");

    ctx.drawImage(
        image, 
        0,0,
        800, 340

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

    // Call the clearCanvas function whenever you want to clear the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const newCanvas = canvas.cloneNode(true);
    canvas.parentNode.replaceChild(newCanvas, canvas);
    copyRinkToCanvas();
    const new_ctx = newCanvas.getContext("2d");
    new_ctx.fillStyle = "green";
    // Set the circle border color and width
    new_ctx.strokeStyle = "black"; // Border color
    new_ctx.lineWidth = 2;       // Border width

    // Add a single click event listener to the canvas
    newCanvas.addEventListener("click", function (event) {
        const clickX = event.clientX - newCanvas.getBoundingClientRect().left;
        const clickY = event.clientY - newCanvas.getBoundingClientRect().top;

        data.forEach(element => {
            const x = mapValue(element.coordsX, -100, 100, 0, newCanvas.width);
            const y = mapValue(element.coordsY, -100, 100, 0, newCanvas.height);

            // Calculate the distance between the click point and the center of the circle
            const distance = Math.sqrt(Math.pow(clickX - x, 2) + Math.pow(clickY - y, 2));

            // Check if the click is within the circle
            if (distance <= 5) { // 5 is the radius of the circle
                document.location.href = '/video/' + element.gameId + '-' + element.playId;
            }
        });
    });

    const tooltip = document.getElementById("tooltip");


    newCanvas.addEventListener("mousemove", function (event) {
      const clickX = event.clientX - newCanvas.getBoundingClientRect().left;
      const clickY = event.clientY - newCanvas.getBoundingClientRect().top;

      let hoveredElement = null; // Use a different variable name to avoid confusion

      data.forEach(element => {
          const x = mapValue(element.coordsX, -100, 100, 0, newCanvas.width);
          const y = mapValue(element.coordsY, -100, 100, 0, newCanvas.height);
          
          // Calculate the distance between the click point and the center of the circle
          const distance = Math.sqrt(Math.pow(clickX - x, 2) + Math.pow(clickY - y, 2));


          // Check if the click is within the circle
          if (distance <= 4) { // 5 is the radius of the circle
            hoveredElement = element;
            
          }
      });
      
      if (hoveredElement) {
        newCanvas.style.cursor = "pointer";

        tooltip.style.display = "block";

        tooltip.textContent = hoveredElement.eventDescription;

        const tooltipWidth = tooltip.offsetWidth;
        const tooltipHeight = tooltip.offsetHeight;
        tooltip.style.left = `${mapValue(hoveredElement.coordsX, -100, 100, 0, newCanvas.width) - (tooltipWidth / 2)}px`;
        tooltip.style.top = `${mapValue(hoveredElement.coordsY, -100, 100, 0, newCanvas.height) - tooltipHeight - 6}px`;         
        } else {
          // Change Mouse
          newCanvas.style.cursor = "default";
          // Hide tooltip
          tooltip.style.display = "none";
        }
    });

    data.forEach(element => {
        const x = mapValue(element.coordsX, -100, 100, 0, newCanvas.width);
        const y = mapValue(element.coordsY, -100, 100, 0, newCanvas.height);

        // Draw the circle with a border
        new_ctx.beginPath();
        new_ctx.arc(x, y, 5, 0, Math.PI * 2); // Adjust the circle radius (5) as needed
        new_ctx.fill();
        new_ctx.stroke(); // This line adds the border
        new_ctx.closePath();
    });
}

function copyGoalToCanvas(){
    var canvas = document.querySelector("canvas");
    var goalMarks = document.querySelectorAll("#goal_mark");


    var ctx = canvas.getContext("2d");

    // Loop through the goal marks and draw circles on the canvas
    goalMarks.forEach(function (goalMark, index) {
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
        ctx.arc(x, y, 5, 0, Math.PI * 2); // Adjust the circle radius (5) as needed
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
            if (distance <= 5) { // 5 is the radius of the circle
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
    // Get rink points on load:
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
            updateRink(data[0]);       
          },
          error: function(error) {
            console.error('Error fetching data: ', error);
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





