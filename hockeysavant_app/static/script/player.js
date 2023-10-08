
function yearDropdown() {
    // Set buttons
  const percentileYearButton = document.getElementById("percentile-year");
  const rinkYearButton = document.getElementById("rink-year");
  // Set dropdown menus
  const percentileYearDropdown = document.getElementsByClassName("percentile-year-selector")[0];
  const rinkYearDropdown = document.getElementsByClassName("rink-year-selector")[0];
  // Set options in dropdown menus
  const yearOptions = document.getElementsByClassName("dropdown-select");
  const yearOptionsArray = Array.from(yearOptions);
  // Set year selected
  const yearLabel = document.getElementsByClassName("selected-dropdown");
  const yearLabelArray = Array.from(yearLabel);



  // Create Click event for rink year dropdown
  percentileYearButton.addEventListener("click", function() {
    if (percentileYearDropdown.style.display == 'block') {
      percentileYearDropdown.style.display = 'none';
    } else if (percentileYearDropdown.style.display == 'none') {
      percentileYearDropdown.style.display = 'block';
    }
    
  });
  yearOptionsArray.forEach(function (element) {
    element.addEventListener("click", function () {
      yearLabel.innerHTML = element.innerText;
      yearLabel[0].attributes.value = element.attributes[0];
      yearLabel[1].attributes.value = element.attributes[0];
    });
  });
  // Create Click event for rink year dropdown
  rinkYearButton.addEventListener("click", function() {
    if (rinkYearDropdown.style.display == 'block') {
      rinkYearDropdown.style.display = 'none';
    } else if (rinkYearDropdown.style.display == 'none') {
      rinkYearDropdown.style.display = 'block';
    }
  });
  yearOptionsArray.forEach(function (element) {
    element.addEventListener("click", function () {

      yearLabelArray[0].innerHTML = element.innerText;
      yearLabelArray[0].setAttribute('value', element.getAttribute('data-value'))

      yearLabelArray[1].innerHTML = element.innerText;
      yearLabelArray[1].setAttribute('value', element.getAttribute('data-value'))
      
    });
  });
  }

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
    const rink_container = document.getElementById("rink");
    const canvas = document.getElementById("rink_canvas");
    const ctx = canvas.getContext("2d");
    const CIRCLE_RADIUS = 5;

    // Call the clearCanvas function whenever you want to clear the canvas
    ctx.clearRect(0, 0, rink_container.clientWidth, rink_container.clientWidth * .425);
    const newCanvas = canvas.cloneNode(true);
    canvas.parentNode.replaceChild(newCanvas, canvas);
    copyRinkToCanvas(rink_container.clientWidth, rink_container.clientWidth * .425);
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
            const x = mapValue(dataElement.coordsX, -100, 100, 0, rink_container.clientWidth);
            const y = mapValue(-dataElement.coordsY, -100, 100, 0, rink_container.clientWidth * .425);
            
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
          const x = mapValue(dataElement.coordsX, -100, 100, 0, rink_container.clientWidth);
          const y = mapValue(-dataElement.coordsY, -100, 100, 0, rink_container.clientWidth * .425);
          
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
    data.forEach(dataElement => {
        const x = mapValue(dataElement.coordsX, -100, 100, 0, rink_container.clientWidth);
        const y = mapValue(-dataElement.coordsY, -100, 100, 0, rink_container.clientWidth * .425);
        
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

function requestRinkData($) {
  // Check if the data is already cached
  if (cachedRinkData) {
    updateRink(cachedRinkData);
  } else {
    const player_id = $('.player_info').attr('id');
    const strength_type = $('.event-filter.active').attr('name');
    const highlight_type = $('.strength-filter.active').attr('name');
    const year = $('.selected-dropdown')[0].attributes.value.textContent;

    $.ajax({
      url: '/goal_data/' + player_id,
      type: 'GET',
      dataType: 'json',
      data: {
        highlight: highlight_type,
        strength: strength_type,
        year: year
      },
      success: function(data) {
        // Cache the data
        cachedRinkData = data;
        
        // Handle the data received from the server
        // Update the HTML on the /players page with the data
        updateRink(data);
      },
      error: function(error) {
        console.error('Error fetching goal data: ', error);
      }
    });
  }
}
function requestPercentileData($) {
  const player_id = $('.player_info').attr('id');
  const year = $('.selected-dropdown')[0].attributes.value.textContent;

  $.ajax({
      url: '/skater_percentile/' + player_id,
      type: 'GET',
      dataType: 'json',
      data: {
        year: year
      },
      success: function(data) {
      // Handle the data received from the server
      // Update the HTML on the /players page with the data
      updatePercentileGraph(data);
      },
      error: function(error) {
      console.error('Error fetching percentile data: ', error);
      }
  });
    
}
function requestPlayerData($) {
  requestPercentileData($);
  requestRinkData($);
}




let cachedRinkData = null;
const rink_container = document.getElementById("rink");
  

// Code for rink updating 
// TODO - add more info to the tool tip
// TODO - add season filter
// TODO - add en filter 
jQuery(document).ready(function($) {
  // Year select
  yearDropdown();
  
  // Get rink points on load:
  setTimeout(requestPlayerData($), 1);
  
  rink_container.style.height = rink_container.clientWidth *.425 + 'px'


  $(window).on('resize', function() {
    rink_container.style.height = rink_container.clientWidth *.425 + 'px'
    requestRinkData($);
  });
  
  $('.dropdown-select').click(function(){
    cachedRinkData = null;
    setTimeout(requestPlayerData($), 1);
  })
  
  $('.btn.video-filter').click(function(){
    // Add small wait to make sure the button clicked is the active button
    setTimeout(function() {
    const strength_type = $('.event-filter.active').attr('name');
    const highlight_type = $('.strength-filter.active').attr('name');
    const player_id = $('.player_info').attr('id');
    const year = $('.selected-dropdown')[0].attributes.value.textContent;
  
    $.ajax({
        url: '/goal_data/' + player_id,
        type: 'GET',
        dataType: 'json',
        data: {
          highlight: highlight_type,
          strength: strength_type,
          year: year
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


