function is_valid_guess(guess) {
    return guess in CHOICES;
}

function get_previous_guess_element(i) {
    return document.getElementById("previous_guess" + i);
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

function get_text_for_comparison(x) {
    if (x < 0) {
        // Needs to be bigger
        return UP;
    }
    if (x > 0) {
        // Needs to be smaller
        return DOWN;
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

function get_guess_suffix(guess) {
    if (guess == TARGET) {
        return MEDAL + " " + MEDAL + " " + MEDAL;
    }
    var choice = CHOICES[guess];

    var result = "";

    result += get_text_for_comparison(choice["length"]) + " ";
    result += get_text_for_comparison(choice["height"]) + " ";
    result += get_text_for_distance(choice["distance"]) + " ";
    result += get_text_for_bearing(choice["bearing"]);

    return result;
}

window.onload = function() {
  twemoji.parse(document.body);
  var num_previous_guesses = 0;

  var submit_element = document.getElementById("submit");
  var guess_element = document.getElementById("guess");
  var previous_guesses = [];

  submit_element.onclick = function() {
      var guess = guess_element.value;
      guess_element.value = "";
      if (previous_guesses.includes(guess) || !is_valid_guess(guess)) {
          return;
      }
      console.log(guess);
      console.log(previous_guesses);
      previous_guesses.push(guess);
      get_previous_guess_element(num_previous_guesses).textContent = guess + get_guess_suffix(guess);
      num_previous_guesses++;

      twemoji.parse(document.body);
  };
}
