const test = require("node:test");
const assert = require("node:assert/strict");

const WeatherActions = require("../src/renderer/editorWeatherActions.js");

test("weatherErrorMessage joins response errors and falls back to a default message", () => {
  assert.equal(WeatherActions.weatherErrorMessage({ errors: ["one", "two"] }), "one\ntwo");
  assert.equal(WeatherActions.weatherErrorMessage({ errors: [] }), "Weather fetch failed");
  assert.equal(WeatherActions.weatherErrorMessage(null), "Weather fetch failed");
});

test("applyWeatherResponse stores weather dummy data and formats status details", () => {
  const state = { layout: {} };

  const result = WeatherActions.applyWeatherResponse(state, {
    ok: true,
    weather: { temp_c: 21.6, condition: "Clear" },
    location: { source: "browser" },
  });

  assert.equal(result.applied, true);
  assert.deepEqual(state.layout.dummy_data.weather, { temp_c: 21.6, condition: "Clear" });
  assert.equal(result.tempText, "22°C");
  assert.equal(result.locationSource, "browser");
});

test("applyWeatherResponse preserves existing dummy data", () => {
  const state = {
    layout: {
      dummy_data: {
        vehicle: { speed_kmh: 42 },
      },
    },
  };

  WeatherActions.applyWeatherResponse(state, {
    ok: true,
    weather: { temp_c: "not numeric" },
    location: {},
  });

  assert.deepEqual(state.layout.dummy_data.vehicle, { speed_kmh: 42 });
  assert.deepEqual(state.layout.dummy_data.weather, { temp_c: "not numeric" });
});

test("requestBrowserLocation resolves null when geolocation is unavailable", async () => {
  const result = await WeatherActions.requestBrowserLocation({});

  assert.equal(result, null);
});

test("requestBrowserLocation normalizes successful browser coordinates", async () => {
  const navigatorRef = {
    geolocation: {
      getCurrentPosition(success, _failure, options) {
        assert.deepEqual(options, {
          enableHighAccuracy: true,
          maximumAge: 60_000,
          timeout: 3_500,
        });
        success({
          coords: {
            latitude: 37.5,
            longitude: 127.1,
            accuracy: 11,
          },
        });
      },
    },
  };

  const result = await WeatherActions.requestBrowserLocation(navigatorRef);

  assert.deepEqual(result, {
    latitude: 37.5,
    longitude: 127.1,
    accuracy: 11,
    source: "browser",
  });
});

test("requestBrowserLocation resolves null on browser geolocation failure", async () => {
  const navigatorRef = {
    geolocation: {
      getCurrentPosition(_success, failure) {
        failure(new Error("denied"));
      },
    },
  };

  const result = await WeatherActions.requestBrowserLocation(navigatorRef);

  assert.equal(result, null);
});

function commandDeps(log = []) {
  return {
    recordHistory() {
      log.push(["recordHistory"]);
    },
    markDirty() {
      log.push(["markDirty"]);
    },
    renderAll() {
      log.push(["renderAll"]);
    },
    schedulePreview(delay) {
      log.push(["schedulePreview", delay]);
    },
    setStatus(message, kind = "") {
      log.push(["setStatus", message, kind]);
    },
    translate(key) {
      return `t:${key}`;
    },
  };
}

test("fetchWeatherCommand applies successful weather response and updates status", async () => {
  const log = [];
  const state = { layout: { dummy_data: { vehicle: { speed_kmh: 42 } } } };
  const service = {
    fetchWeather(payload) {
      log.push(["fetchWeather", payload]);
      return Promise.resolve({
        ok: true,
        weather: { temp_c: 19.4, condition: "Cloudy" },
        location: { source: "network" },
      });
    },
  };

  const result = await WeatherActions.fetchWeatherCommand(state, service, {}, commandDeps(log));

  assert.equal(result.ok, true);
  assert.equal(result.changed, true);
  assert.deepEqual(state.layout.dummy_data.vehicle, { speed_kmh: 42 });
  assert.deepEqual(state.layout.dummy_data.weather, { temp_c: 19.4, condition: "Cloudy" });
  assert.deepEqual(log, [
    ["setStatus", "t:weatherLoading", ""],
    ["fetchWeather", { layout: state.layout, browserLocation: null }],
    ["recordHistory"],
    ["markDirty"],
    ["renderAll"],
    ["schedulePreview", 30],
    ["setStatus", "t:weatherReady · 19°C · network", "ok"],
  ]);
});

test("fetchWeatherCommand reports service errors without dirtying layout", async () => {
  const log = [];
  const state = { layout: {} };
  const service = {
    fetchWeather() {
      log.push(["fetchWeather"]);
      return Promise.resolve({ ok: false, errors: ["offline"] });
    },
  };

  const result = await WeatherActions.fetchWeatherCommand(state, service, {}, commandDeps(log));

  assert.equal(result.ok, false);
  assert.equal(result.changed, false);
  assert.equal(result.errorMessage, "offline");
  assert.equal(state.layout.dummy_data, undefined);
  assert.deepEqual(log, [
    ["setStatus", "t:weatherLoading", ""],
    ["fetchWeather"],
    ["setStatus", "offline", "error"],
  ]);
});

test("fetchWeatherCommand reports thrown errors", async () => {
  const log = [];
  const state = { layout: {} };
  const service = {
    fetchWeather() {
      throw new Error("weather crashed");
    },
  };

  const result = await WeatherActions.fetchWeatherCommand(state, service, {}, commandDeps(log));

  assert.equal(result.ok, false);
  assert.equal(result.errorMessage, "weather crashed");
  assert.deepEqual(log, [
    ["setStatus", "t:weatherLoading", ""],
    ["setStatus", "weather crashed", "error"],
  ]);
});
