(function exposeEditorScreenState(globalScope) {
  function ensureScreens(layout, currentScreen = "standalone") {
    const baseElements = clone(layout.elements || []);
    if (!layout.screens || typeof layout.screens !== "object" || Array.isArray(layout.screens)) {
      layout.screens = {};
    }
    for (const [screen, label] of [
      ["standalone", "Standalone vehicle HUD"],
      ["bridge", "Bridge navigation HUD"],
    ]) {
      if (!layout.screens[screen] || typeof layout.screens[screen] !== "object") {
        layout.screens[screen] = { label, elements: clone(baseElements) };
      }
      if (!Array.isArray(layout.screens[screen].elements)) {
        layout.screens[screen].elements = clone(baseElements);
      }
    }
    const selected = layout.screens[currentScreen] ? currentScreen : "standalone";
    layout.elements = clone(layout.screens[selected].elements);
    return selected;
  }

  function syncCurrentScreen(layout, currentScreen) {
    if (!layout.screens || typeof layout.screens !== "object" || Array.isArray(layout.screens)) {
      layout.screens = {};
    }
    if (!layout.screens[currentScreen] || typeof layout.screens[currentScreen] !== "object") {
      layout.screens[currentScreen] = { label: titleCase(currentScreen), elements: [] };
    }
    layout.screens[currentScreen].elements = clone(layout.elements || []);
  }

  function switchScreen(layout, fromScreen, toScreen) {
    syncCurrentScreen(layout, fromScreen);
    const selected = layout.screens[toScreen] ? toScreen : "standalone";
    layout.elements = clone(layout.screens[selected].elements || []);
    return selected;
  }

  function importOtherScreen(layout, currentScreen) {
    syncCurrentScreen(layout, currentScreen);
    const other = currentScreen === "standalone" ? "bridge" : "standalone";
    layout.screens[currentScreen].elements = clone(layout.screens[other].elements || []);
    layout.elements = clone(layout.screens[currentScreen].elements);
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function titleCase(value) {
    return String(value || "")
      .replace(/[_-]+/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  const api = {
    ensureScreens,
    syncCurrentScreen,
    switchScreen,
    importOtherScreen,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorScreenState = api;
})(typeof window !== "undefined" ? window : globalThis);
