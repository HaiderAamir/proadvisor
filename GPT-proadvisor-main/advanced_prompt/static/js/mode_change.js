$(document).ready(function () {
  // Check and set the initial state from localStorage
  const savedState = localStorage.getItem('darkMode');
  if (savedState === 'off') {
    toggleDarkMode();
  }
  else {
    document.getElementById('darkModeSwitch').checked = true;
  }

});

// Event listener for the toggle switch
const darkModeSwitch = document.getElementById('darkModeSwitch');
darkModeSwitch.addEventListener('change', toggleDarkMode);


// Function to toggle the icons and store the state
function toggleDarkMode() {
  const darkModeSwitch = document.getElementById('darkModeSwitch');
  const dayIcon = document.getElementById('dayIcon');
  const nightIcon = document.getElementById('nightIcon');

  if (darkModeSwitch.checked) {
    // Toggle switch is on (night mode)
    dayIcon.style.display = 'none';
    nightIcon.style.display = 'inline';
    // Store the state in localStorage
    localStorage.setItem('darkMode', 'on');
    darkModeSwitch.checked = true;
  } else {
    // Toggle switch is off (day mode)
    dayIcon.style.display = 'inline';
    nightIcon.style.display = 'none';
    // Store the state in localStorage
    localStorage.setItem('darkMode', 'off');
    darkModeSwitch.checked = false;

  }

  modeChange();
}


// change the
function modeChange() {

  // localStorage.setItem('darkMode', 'off');
  var darkMode = localStorage.getItem('darkMode');
  //alert('hello')
  if (darkMode === 'on') {
    // Get the link element with the id "mode_change"
    var linkElement = $('#mode_change');

    // Assign the src attribute with the value "{% static 'css/lightmode.css' %}/"
    linkElement.attr('href', "");

  } else {
    // Get the link element with the id "mode_change"
    var linkElement = $('#mode_change');

    // Assign the src attribute with the value "{% static 'css/lightmode.css' %}/"
    linkElement.attr('href', "../static/css/lightmode.css");
  }
}
