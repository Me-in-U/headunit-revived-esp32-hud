const OPEN_METEO_CURRENT_FIELDS = [
  "temperature_2m",
  "apparent_temperature",
  "weather_code",
  "wind_speed_10m",
];

const WEATHER_CODES = {
  0: ["Clear sky", "맑음"],
  1: ["Mainly clear", "대체로 맑음"],
  2: ["Partly cloudy", "구름 조금"],
  3: ["Overcast", "흐림"],
  45: ["Fog", "안개"],
  48: ["Depositing rime fog", "상고대 안개"],
  51: ["Light drizzle", "약한 이슬비"],
  53: ["Drizzle", "이슬비"],
  55: ["Dense drizzle", "강한 이슬비"],
  61: ["Light rain", "약한 비"],
  63: ["Rain", "비"],
  65: ["Heavy rain", "강한 비"],
  71: ["Light snow", "약한 눈"],
  73: ["Snow", "눈"],
  75: ["Heavy snow", "강한 눈"],
  80: ["Rain showers", "소나기"],
  81: ["Rain showers", "소나기"],
  82: ["Violent rain showers", "강한 소나기"],
  95: ["Thunderstorm", "뇌우"],
  96: ["Thunderstorm with hail", "우박 동반 뇌우"],
  99: ["Thunderstorm with hail", "우박 동반 뇌우"],
};

function numberOrNull(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function normalizeLocation(candidate, defaults = {}) {
  if (!candidate || typeof candidate !== "object") {
    return null;
  }
  const latitude = numberOrNull(candidate.latitude ?? candidate.lat);
  const longitude = numberOrNull(candidate.longitude ?? candidate.lon ?? candidate.lng);
  if (latitude === null || longitude === null) {
    return null;
  }
  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
    return null;
  }
  return {
    latitude,
    longitude,
    accuracy: numberOrNull(candidate.accuracy) ?? defaults.accuracy ?? 1000,
    source: String(candidate.source || defaults.source || "layout"),
    name: candidate.name || candidate.city || candidate.location_name || defaults.name || "",
  };
}

function layoutLocationCandidates(layout) {
  const dummy = layout?.dummy_data || {};
  return [
    normalizeLocation(dummy.bridge?.location, { source: "bridge", accuracy: 10 }),
    normalizeLocation(dummy.location, { source: "bridge", accuracy: 20 }),
    normalizeLocation(dummy.nav?.location, { source: "bridge", accuracy: 20 }),
    normalizeLocation(dummy.vehicle?.location, { source: "vehicle", accuracy: 30 }),
    normalizeLocation(dummy.nav, { source: "nav", accuracy: 1000 }),
    normalizeLocation(dummy.vehicle, { source: "vehicle", accuracy: 1000 }),
  ].filter(Boolean);
}

function chooseBestLocation({ layout, browserLocation, ipLocation } = {}) {
  const candidates = [
    ...layoutLocationCandidates(layout),
    normalizeLocation(browserLocation, { source: "browser", accuracy: 100 }),
    normalizeLocation(ipLocation, { source: "network", accuracy: 50000 }),
  ].filter(Boolean);
  if (!candidates.length) {
    return null;
  }
  return candidates.sort((left, right) => {
    const accuracyDelta = Number(left.accuracy) - Number(right.accuracy);
    if (accuracyDelta !== 0) {
      return accuracyDelta;
    }
    return sourceRank(left.source) - sourceRank(right.source);
  })[0];
}

function sourceRank(source) {
  if (source === "bridge") {
    return 0;
  }
  if (source === "browser") {
    return 1;
  }
  if (source === "vehicle" || source === "nav") {
    return 2;
  }
  return 3;
}

function buildOpenMeteoUrl(location) {
  const url = new URL("https://api.open-meteo.com/v1/forecast");
  url.searchParams.set("latitude", String(location.latitude));
  url.searchParams.set("longitude", String(location.longitude));
  url.searchParams.set("current", OPEN_METEO_CURRENT_FIELDS.join(","));
  url.searchParams.set("timezone", "auto");
  return url.toString();
}

function weatherCodeLabel(code) {
  const labels = WEATHER_CODES[Number(code)] || ["Unknown", "알 수 없음"];
  return { en: labels[0], ko: labels[1] };
}

function normalizeWeather(openMeteoPayload, location) {
  const current = openMeteoPayload?.current || {};
  const code = numberOrNull(current.weather_code);
  const labels = weatherCodeLabel(code);
  return {
    temp_c: numberOrNull(current.temperature_2m),
    apparent_c: numberOrNull(current.apparent_temperature),
    wind_kmh: numberOrNull(current.wind_speed_10m),
    code,
    condition: labels.en,
    condition_ko: labels.ko,
    location_name: location.name || coordinateLabel(location),
    latitude: location.latitude,
    longitude: location.longitude,
    source: location.source,
    updated_at: current.time || new Date().toISOString(),
  };
}

function coordinateLabel(location) {
  return `${Number(location.latitude).toFixed(3)}, ${Number(location.longitude).toFixed(3)}`;
}

module.exports = {
  OPEN_METEO_CURRENT_FIELDS,
  chooseBestLocation,
  buildOpenMeteoUrl,
  normalizeWeather,
  weatherCodeLabel,
  normalizeLocation,
};
