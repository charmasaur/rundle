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

function get_text_for_length(x) {
    if (x < 0) {
        // Needs to be bigger
        return PLUS;
    }
    if (x > 0) {
        // Needs to be smaller
        return MINUS;
    }
    return GREEN;
}

function get_text_for_elevation(x) {
    if (x < 0) {
        // Needs to be bigger
        return MOUNTAIN;
    }
    if (x > 0) {
        // Needs to be smaller
        return BEACH;
    }
    return GREEN;
}

function get_text_for_distance(x) {
    if (x == 0) {
        return GREEN;
    }
    return x + "km"
}

function get_text_for_bearing(x) {
    var half_width = 45/2;

    if (x >= -half_width && x < half_width) {
        return UP;
    }
    if (x >= 45-half_width && x < 45+half_width) {
        return UP_RIGHT;
    }
    if (x >= 90-half_width && x < 90+half_width) {
        return RIGHT;
    }
    if (x >= 135-half_width && x < 135+half_width) {
        return DOWN_RIGHT;
    }
    if (x >= 180-half_width && x < -180+half_width) {
        return DOWN;
    }
    if (x >= -135-half_width && x < -135+half_width) {
        return DOWN_LEFT;
    }
    if (x >= -90-half_width && x < -90+half_width) {
        return LEFT;
    }
    if (x >= -45-half_width && x < -45+half_width) {
        return UP_LEFT;
    }
    // I guess this could happen if we get unlucky with floating point.
    return UP_LEFT;
}

function get_guess_hints(guess) {
    if (guess == TARGET) {
        return [MEDAL, MEDAL, MEDAL, MEDAL];
    }
    var choice = CHOICES[guess];

    var result = [];

    result.push(get_text_for_length(choice["length"]));
    result.push(get_text_for_elevation(choice["elevation"]));
    result.push(get_text_for_distance(choice["distance"]));
    result.push(get_text_for_bearing(choice["bearing"]));

    return result;
}

window.onload = function() {
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

      var hints = get_guess_hints(guess);
      var previous_guess_element = document.getElementById("previous_guess_" + num_previous_guesses);
      previous_guess_element.textContent = guess;

      for (var i = 0; i < hints.length; i++) {
        let td = document.getElementById("hint_" + num_previous_guesses + "_" + i);
        td.textContent = hints[i];
        td.style.contentVisibility = 'hidden';
        setTimeout(function() { td.style.contentVisibility = 'visible'; }, (i+1)*DELAY_PER_HINT);
      }

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
          }, (hints.length + 1) * DELAY_PER_HINT);
      }

      twemoji.parse(document.body);

      return false;
  };
}
