(function exposeEditorWeatherActions(globalScope) {
  const GEOLOCATION_OPTIONS = {
    enableHighAccuracy: true,
    maximumAge: 60_000,
    timeout: 3_500,
  };

  function weatherErrorMessage(response) {
    if (Array.isArray(response?.errors) && response.errors.length > 0) {
      return response.errors.join("\n");
    }
    return "Weather fetch failed";
  }

  function applyWeatherResponse(state, response) {
    state.layout.dummy_data = state.layout.dummy_data || {};
    state.layout.dummy_data.weather = response.weather;
    const temp = Number(response.weather?.temp_c);
    return {
      applied: true,
      tempText: Number.isFinite(temp) ? `${Math.round(temp)}°C` : "",
      locationSource: response.location?.source || "",
    };
  }

  function requestBrowserLocation(navigatorRef) {
    if (!navigatorRef?.geolocation) {
      return Promise.resolve(null);
    }
    return new Promise((resolve) => {
      navigatorRef.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            source: "browser",
          });
        },
        () => resolve(null),
        GEOLOCATION_OPTIONS
      );
    });
  }

  async function fetchWeatherCommand(state, service, navigatorRef, deps) {
    deps.setStatus(deps.translate("weatherLoading"));
    try {
      const browserLocation = await requestBrowserLocation(navigatorRef);
      const response = await service.fetchWeather({
        layout: state.layout,
        browserLocation,
      });
      if (!response.ok) {
        const message = weatherErrorMessage(response);
        deps.setStatus(message, "error");
        return { ok: false, changed: false, errorMessage: message };
      }
      deps.recordHistory();
      const weatherResult = applyWeatherResponse(state, response);
      deps.markDirty();
      deps.renderAll();
      deps.schedulePreview(30);
      const status = `${deps.translate("weatherReady")}${weatherResult.tempText ? ` · ${weatherResult.tempText}` : ""} · ${weatherResult.locationSource}`;
      deps.setStatus(status, "ok");
      return { ok: true, changed: true, status, weatherResult };
    } catch (error) {
      const message = error.message || String(error);
      deps.setStatus(message, "error");
      return { ok: false, changed: false, errorMessage: message };
    }
  }

  const api = {
    applyWeatherResponse,
    fetchWeatherCommand,
    requestBrowserLocation,
    weatherErrorMessage,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorWeatherActions = api;
})(typeof window !== "undefined" ? window : globalThis);
