const test = require("node:test");
const assert = require("node:assert/strict");

const {
  OPEN_METEO_CURRENT_FIELDS,
  buildOpenMeteoUrl,
  chooseBestLocation,
  normalizeWeather,
  weatherCodeLabel,
} = require("../src/weather");

test("weather location selection prefers the most accurate available source", () => {
  const layout = {
    dummy_data: {
      bridge: {
        location: { latitude: 37.5, longitude: 127.0, accuracy: 30, source: "bridge" },
      },
    },
  };

  const selected = chooseBestLocation({
    layout,
    browserLocation: { latitude: 37.6, longitude: 127.1, accuracy: 8, source: "browser" },
    ipLocation: { latitude: 35, longitude: 128, source: "network" },
  });

  assert.equal(selected.source, "browser");
  assert.equal(selected.latitude, 37.6);
});

test("weather location falls back to network location when precise sources are absent", () => {
  const selected = chooseBestLocation({
    layout: { dummy_data: {} },
    ipLocation: { latitude: 35.1, longitude: 129.1, city: "Busan", source: "network" },
  });

  assert.equal(selected.source, "network");
  assert.equal(selected.name, "Busan");
});

test("open meteo url requests current weather fields", () => {
  const url = new URL(buildOpenMeteoUrl({ latitude: 37.5, longitude: 127.0 }));

  assert.equal(url.origin + url.pathname, "https://api.open-meteo.com/v1/forecast");
  assert.equal(url.searchParams.get("latitude"), "37.5");
  assert.equal(url.searchParams.get("longitude"), "127");
  assert.equal(url.searchParams.get("current"), OPEN_METEO_CURRENT_FIELDS.join(","));
});

test("weather payload normalizes labels and numeric values", () => {
  const weather = normalizeWeather(
    { current: { time: "2026-06-03T09:00", temperature_2m: 21.4, apparent_temperature: 23, weather_code: 1, wind_speed_10m: 9.2 } },
    { latitude: 37.5, longitude: 127.0, source: "browser", name: "Seoul" }
  );

  assert.equal(weather.temp_c, 21.4);
  assert.equal(weather.condition, "Mainly clear");
  assert.equal(weather.condition_ko, "대체로 맑음");
  assert.equal(weather.location_name, "Seoul");
  assert.deepEqual(weatherCodeLabel(999), { en: "Unknown", ko: "알 수 없음" });
});
