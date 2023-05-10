const DELAY_PER_HINT = 300;
const STATS_DELAY = 500;
const TOAST_DELAY = 1000;

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
    if (bearing >= 180-half_width || bearing < -180+half_width) {
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
 * Converts hint contents codes to hint text/emoji.
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
 */
function convert_guess_hints(hint_contents) {
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

    return funcs.map((f, i) => f(hint_contents[1+i]));
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

  close_help = function() {
    help.classList.add("hidden");
  }
  open_help = function() {
    help.classList.remove("hidden");
    put_storage_item("shown_help", true);
  }

  document.getElementById("close_help").onclick = close_help;
  document.getElementById("open_help").onclick = open_help;

  if (get_storage_item("shown_help", "false") == "false") {
    open_help();
  }
}

function populate_stats(history) {
  // To make things simpler, ignore any history from after "today", and sort by date.
  history = history.filter(h => h["date"] <= RUN_DATE).sort((a, b) => new Date(a["date"]).getTime() - new Date(b["date"]).getTime());

  const played = history.length;
  const played_dates = history.map(h => h["date"]);

  const won_days = history.filter(h => h["success"] == true);
  const won = won_days.length;
  const won_dates = won_days.map(h => h["date"]);

  if (won == 0) {
    var best_streak = 0;
    var current_streak = 0;
  } else {
    var streaks = [1];
    var previous_date = new Date(won_dates[0]);
    for (var date of won_dates.slice(1)) {
      previous_date.setDate(previous_date.getDate() + 1);
      if (previous_date.toISOString().substr(0, 10) == date) {
        streaks[streaks.length - 1]++;
      } else {
        streaks.push(1);
        previous_date = new Date(date);
      }
    }

    var best_streak = Math.max(...streaks);
    var current_streak = played_dates.at(-1) == won_dates.at(-1) ? streaks.at(-1) : 0;
  }

  document.getElementById("stats_played").textContent = played;
  document.getElementById("stats_win").textContent =
        played == 0 ? 0 : ((won/played)*100).toFixed(0);
  document.getElementById("stats_current_streak").textContent = current_streak;
  document.getElementById("stats_best_streak").textContent = best_streak;
}

function show_stats() {
  const stats = document.getElementById("stats");
  stats.classList.remove("hidden");
}

function init_stats() {
  const stats = document.getElementById("stats");

  populate_stats(load_history());

  close_stats = function() {
    stats.classList.add("hidden");
  }
  open_stats = function() {
    show_stats();
  }

  document.getElementById("close_stats").onclick = close_stats;
  document.getElementById("open_stats").onclick = open_stats;
}

function init_share(guesses) {
  const button = document.getElementById("share_button");
  const toast = document.getElementById("share_toast");

  share = function() {
    const result = [];
    result.push("Rundle " + RUN_DATE);
    for (const guess of guesses) {
      const row = [];
      convert_guess_hints(get_guess_hint_contents(guess))
         .map((content, i) => {
           if (i > 0) {
             row.push(content);
           }
         });
      result.push(row.join(" "));
    }

    navigator.clipboard.writeText(result.join("\n"))
      .then(() => {
          button.classList.add("hidden");
          toast.classList.remove("hidden");
          setTimeout(() => {
              toast.classList.add("hidden");
              button.classList.remove("hidden");
          }, TOAST_DELAY);
      });
  }

  document.getElementById("share_container").classList.remove("hidden");
  button.onclick = share;
}

function init_map() {
  const map_modal = document.getElementById("map");
  const map_display = document.getElementById("map_display");

  mapboxgl.accessToken = MAPBOX_API_KEY;
  var target_position = {lat: TARGET_DETAILS['lat'], lng: TARGET_DETAILS['lng']};
  var map = new mapboxgl.Map({
      container: map_display,
      center: target_position,
      zoom: 10,
      style: 'mapbox://styles/mapbox/outdoors-v12'
  });

  map.on('load', () => {
      if (TARGET_DETAILS["latitudes"].length == 0) {
          return;
      }
      map.addSource('route', {
          'type': 'geojson',
          'data': {
              'type': 'Feature',
              'properties': {},
              'geometry': {
                  'type': 'LineString',
                  'coordinates': TARGET_DETAILS["latitudes"].map(
                      (lat, i) => [TARGET_DETAILS["longitudes"][i], lat]),
              },
          },
      });
      map.addLayer(
          { 'id': 'route',
              'type': 'line',
              'source': 'route',
              'layout': {
                  'line-join': 'round',
                  'line-cap': 'round',
              },
              'paint': { 'line-color': '#f00', 'line-width': 3 },
          },
          // Position just below the labels.
          "poi-label");
  });

  var marker = new mapboxgl.Marker()
      .setLngLat(target_position)
      .addTo(map);

  close_map = function() {
    map_modal.classList.add("hidden");
  }
  open_map = function() {
    map_modal.classList.remove("hidden");
    map.resize();
  }

  document.getElementById("close_map").onclick = close_map;
  document.getElementById("open_map").onclick = open_map;
}

function save_state(guesses) {
  put_storage_item("guesses", JSON.stringify(guesses));
  put_storage_item("date", RUN_DATE);
}

function load_state() {
  if (get_storage_item("date", "") == RUN_DATE) {
    return JSON.parse(get_storage_item("guesses", "[]"))
  }
  return [];
}

function load_history() {
  return JSON.parse(get_storage_item("rundle_history", "[]"));
}

function update_history(guesses, success) {
  new_history_item = {
      "date": RUN_DATE,
      "success": success,
      "guesses": guesses,
      "target": TARGET,
      "target_details": {
          "length": TARGET_DETAILS["length"],
          "elevation": TARGET_DETAILS["elevation"],
          "lat": TARGET_DETAILS["lat"],
          "lng": TARGET_DETAILS["lng"],
      },
      "num_guesses": NUM_GUESSES,
  }

  rundle_history = load_history()
  // If we already have history for today, replace it to avoid messing up stats.
  const index = rundle_history.findIndex(h => h["date"] == RUN_DATE);
  if (index >= 0) {
    rundle_history.splice(index, 1, new_history_item);
  } else {
    rundle_history.push(new_history_item);
  }
  put_storage_item("rundle_history", JSON.stringify(rundle_history));
  populate_stats(rundle_history);
}

window.onload = function() {
  init_help();
  init_stats();

  // Populate help page.
  const examples = document.getElementsByName("help_example");
  for (const example of examples) {
      convert_guess_hints(example.dataset.hintContents.split(","))
          .map((content, i) => example.cells[i].textContent = content);
  }

  var num_previous_guesses = 0;

  var guess_form_element = document.getElementById("guess_form");
  var answer_element = document.getElementById("answer");
  var answer_container_element = document.getElementById("answer_container");
  var guess_form_button_element = document.getElementById("guess_form_button");
  var guess_element = document.getElementById("guess");
  var previous_guesses = [];

  var done = false;

  apply_guess = function(guess, is_realtime) {
      guess_element.value = "";
      if (previous_guesses.includes(guess) || !is_valid_guess(guess)) {
          return false;
      }
      previous_guesses.push(guess);

      let row = document.getElementById("hint_" + num_previous_guesses)
      convert_guess_hints(get_guess_hint_contents(guess))
         .map((content, i) => {
            const cell = row.cells[i]
            cell.textContent = content;
            if (i == 0) {
                return;
            }
            if (is_realtime) {
              cell.style.contentVisibility = 'hidden';
              setTimeout(function() { cell.style.contentVisibility = 'visible'; }, i*DELAY_PER_HINT);
            } else {
              cell.style.contentVisibility = 'visible';
            }
          });

      num_previous_guesses++;

      if (num_previous_guesses == NUM_GUESSES || guess == TARGET) {
          done = true;
          guess_form_button_element.disabled = true;
          show_answer = function() {
              guess_form.hidden = true;
              answer_element.innerHTML =
                  TARGET
                  + "<br>" +
                  TARGET_DETAILS["length"]
                  + "km "
                  + TARGET_DETAILS["elevation"]
                  + "m";
              answer_container_element.classList.remove("hidden");
              init_map();
          };
          if (is_realtime) {
            const answer_delay = document.getElementById("hint_0").cells.length * DELAY_PER_HINT
            setTimeout(show_answer, answer_delay);
            setTimeout(show_stats, answer_delay + STATS_DELAY);
            update_history(previous_guesses, guess == TARGET);
          } else {
            show_answer();
          }
          init_share(previous_guesses);
      }
  };

  guess_form_element.onsubmit = function() {
      if (done) {
          // Shouldn't really be necessary, but I don't know what sort of multithreading might be
          // going on, so best to be defensive.
          return false;
      }
      var guess = guess_element.value;
      apply_guess(guess, true);

      twemoji.parse(document.body);

      save_state(previous_guesses);

      return false;
  };

  for (const guess of load_state()) {
    apply_guess(guess, false);
  }

  twemoji.parse(document.body);
}
