const DELAY_PER_HINT = 300;

function is_valid_guess(guess) {
    return guess in CHOICES;
}

UP = twemoji.convert.fromCodePoint("2B06") + twemoji.convert.fromCodePoint("fe0f");
DOWN = twemoji.convert.fromCodePoint("2B07") + twemoji.convert.fromCodePoint("fe0f");
LEFT = twemoji.convert.fromCodePoint("2B05") + twemoji.convert.fromCodePoint("fe0f");
RIGHT = twemoji.convert.fromCodePoint("27A1") + twemoji.convert.fromCodePoint("fe0f");

UP_RIGHT = twemoji.convert.fromCodePoint("2197") + twemoji.convert.fromCodePoint("fe0f");
UP_LEFT = twemoji.convert.fromCodePoint("2196") + twemoji.convert.fromCodePoint("fe0f");
DOWN_RIGHT = twemoji.convert.fromCodePoint("2198") + twemoji.convert.fromCodePoint("fe0f");
DOWN_LEFT = twemoji.convert.fromCodePoint("2199") + twemoji.convert.fromCodePoint("fe0f");
GREEN = twemoji.convert.fromCodePoint("1F7E9");
MEDAL = twemoji.convert.fromCodePoint("1f947");

MOUNTAIN = twemoji.convert.fromCodePoint("26f0");
BEACH = twemoji.convert.fromCodePoint("1f3d6") + twemoji.convert.fromCodePoint("fe0f");
PLUS = twemoji.convert.fromCodePoint("2795");
MINUS = twemoji.convert.fromCodePoint("2796");

function get_code_for_length(x) {
    if (x < 0) {
        // Needs to be bigger
        return "+";
    }
    if (x > 0) {
        // Needs to be smaller
        return "-";
    }
    return "=";
}

function get_code_for_elevation(x) {
    if (x < 0) {
        // Needs to be bigger
        return "+";
    }
    if (x > 0) {
        // Needs to be smaller
        return "-";
    }
    return "=";
}

function get_codes_for_distance_and_bearing(distance, bearing) {
    if (distance == 0) {
        return ["=","="];
    }

    const half_width = 45/2;

    // Might end up using this if we get unlucky with floating point?
    var bearing_code = "N";

    if (bearing >= -half_width && bearing < half_width) {
        bearing_code = "N";
    }
    if (bearing >= 45-half_width && bearing < 45+half_width) {
        bearing_code = "NE";
    }
    if (bearing >= 90-half_width && bearing < 90+half_width) {
        bearing_code = "E";
    }
    if (bearing >= 135-half_width && bearing < 135+half_width) {
        bearing_code = "SE";
    }
    if (bearing >= 180-half_width && bearing < -180+half_width) {
        bearing_code = "S";
    }
    if (bearing >= -135-half_width && bearing < -135+half_width) {
        bearing_code = "SW";
    }
    if (bearing >= -90-half_width && bearing < -90+half_width) {
        bearing_code = "W";
    }
    if (bearing >= -45-half_width && bearing < -45+half_width) {
        bearing_code = "NW";
    }

    return [distance, bearing_code]
}

/**
 * From a guess returns the "hint contents" codes for passing to get_guess_hints.
 */
function get_guess_hint_contents(guess) {
    if (guess == TARGET) {
        return ["y", guess, "=", "=", "=", "="];
    }
    var choice = CHOICES[guess];

    var result = [];
    result.push("n");
    result.push(guess);
    result.push(get_code_for_length(choice["length"]));
    result.push(get_code_for_elevation(choice["elevation"]));
    result.push(...get_codes_for_distance_and_bearing(choice["distance"], choice["bearing"]));

    return result;
}

/**
 * Populates a table row with hints, based on the provided hint contents codes.
 *
 * The hint contents code takes the form:
 * [
 *   <correct (y/n)>,
 *   <name>,
 *   <length (+/-/=)>,
 *   <elevation (+/-/=)>,
 *   <dist (<x>/=)>,
 *   <bearing (N/NE/.../=)>,
 * ]
 *
 * Invokes the callback on each cell if provided.
 */
function populate_guess_hints(row, hint_contents, callback) {
    // Mappings from code to the appropriate character for that part of the hint
    const length_chars = {
        "+": PLUS,
        "-": MINUS,
        "=": GREEN,
    };
    const elevation_chars = {
        "+": MOUNTAIN,
        "-": BEACH,
        "=": GREEN,
    };
    const bearing_chars = {
        "N": UP,
        "NE": UP_RIGHT,
        "E": RIGHT,
        "SE": DOWN_RIGHT,
        "S": DOWN,
        "SW": DOWN_LEFT,
        "W": LEFT,
        "NW": UP_LEFT,
        "=": GREEN,
    };

    const done = hint_contents[0] == 'y';

    // Order of the hint parts in the table
    const funcs = [
        x => x,
        x => done ? MEDAL : length_chars[x],
        x => done ? MEDAL : elevation_chars[x],
        x => done ? MEDAL : (x == "=" ? GREEN : x + "km"),
        x => done ? MEDAL : bearing_chars[x],
    ];

    for (let i = 0; i < row.cells.length; i++) {
        row.cells[i].textContent = funcs[i](hint_contents[1+i]);
        if (typeof callback === 'function') {
            callback(i, row.cells[i]);
        }
    }
}

function get_storage_item(name, def) {
  if (!is_storage_available()) {
    return def;
  }
  var result = localStorage.getItem(name);
  if (result === null) {
    return def;
  }
  return result;
}

function remove_storage_item(name) {
  if (!is_storage_available()) {
    return;
  }
  localStorage.removeItem(name);
}

function put_storage_item(name, val) {
  if (!is_storage_available()) {
    return;
  }
  localStorage.setItem(name, val);
}

function is_storage_available() {
  try {
    localStorage.setItem("test", "test");
    localStorage.removeItem("test");
    return true;
  } catch(e) {
    return false;
  }
}

function init_help() {
  const help = document.getElementById("help");
  const help_open_display = help.style.display;

  close_help = function() {
    help.classList.add("hidden");
  }
  open_help = function() {
    help.classList.remove("hidden");
    put_storage_item("shown_help", true);
  }

  document.getElementById("close_help").onclick = close_help;
  document.getElementById("open_help").onclick = open_help;

  if (!get_storage_item("shown_help", false)) {
    open_help();
  }
}

window.onload = function() {
  init_help();

  // Populate help page.
  const examples = document.getElementsByName("help_example");
  for (const example of examples) {
      populate_guess_hints(example, example.dataset.hintContents.split(","));
  }

  twemoji.parse(document.body);
  var num_previous_guesses = 0;

  var guess_form_element = document.getElementById("guess_form");
  var answer_element = document.getElementById("answer");
  var guess_form_button_element = document.getElementById("guess_form_button");
  var guess_element = document.getElementById("guess");
  var previous_guesses = [];

  var done = false;

  guess_form_element.onsubmit = function() {
      if (done) {
          // Shouldn't really be necessary, but I don't know what sort of multithreading might be
          // going on, so best to be defensive.
          return false;
      }
      var guess = guess_element.value;
      guess_element.value = "";
      if (previous_guesses.includes(guess) || !is_valid_guess(guess)) {
          return false;
      }
      previous_guesses.push(guess);

      populate_guess_hints(
          document.getElementById("hint_" + num_previous_guesses),
          get_guess_hint_contents(guess),
          (i, cell) => {
            if (i == 0) {
                return;
            }
            cell.style.contentVisibility = 'hidden';
            setTimeout(function() { cell.style.contentVisibility = 'visible'; }, i*DELAY_PER_HINT);
          });


      num_previous_guesses++;

      if (num_previous_guesses == NUM_GUESSES || guess == TARGET) {
          done = true;
          guess_form_button_element.disabled = true;
          setTimeout(function() {
            guess_form.hidden = true;
            answer_element.innerHTML =
                  TARGET
                  + "<br>" +
                  TARGET_DETAILS["length"]
                  + "km "
                  + TARGET_DETAILS["elevation"]
                  + "m";
            answer_element.hidden = false;
          }, document.getElementById("hint_0").cells.length * DELAY_PER_HINT);
      }

      twemoji.parse(document.body);

      return false;
  };
}
