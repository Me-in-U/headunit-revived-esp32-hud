(function exposeEditorState(globalScope) {
  const PaletteState =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorPaletteState.js")
      : globalScope.EditorPaletteState;
  const InspectorState =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorInspectorState.js")
      : globalScope.EditorInspectorState;
  const ScreenState =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorScreenState.js")
      : globalScope.EditorScreenState;

  const api = {
    COLOR_KEYS: ["color", "active_color", "inactive_color", "accent", "redline_color"],
    DEFAULT_GEARS: PaletteState.DEFAULT_GEARS,
    VALUE_STYLE_OPTIONS: InspectorState.VALUE_STYLE_OPTIONS,
    GEAR_STYLE_OPTIONS: InspectorState.GEAR_STYLE_OPTIONS,
    clone: PaletteState.clone,
    paletteKey: PaletteState.paletteKey,
    elementFamilyKey: PaletteState.elementFamilyKey,
    elementVariant: PaletteState.elementVariant,
    elementPaletteKey: PaletteState.elementPaletteKey,
    elementPaletteKeys: PaletteState.elementPaletteKeys,
    paletteTemplateMatchesElement: PaletteState.paletteTemplateMatchesElement,
    paletteTemplateMatchesFamily: PaletteState.paletteTemplateMatchesFamily,
    findPaletteElement: PaletteState.findPaletteElement,
    findPaletteFamilyElement: PaletteState.findPaletteFamilyElement,
    groupPaletteFamilies: PaletteState.groupPaletteFamilies,
    uniqueId: PaletteState.uniqueId,
    nextZ: PaletteState.nextZ,
    normalizeElementForCanvas: PaletteState.normalizeElementForCanvas,
    createElement: PaletteState.createElement,
    addOrTogglePaletteElement: PaletteState.addOrTogglePaletteElement,
    inspectorSectionsForElement: InspectorState.inspectorSectionsForElement,
    ensureScreens: ScreenState.ensureScreens,
    syncCurrentScreen: ScreenState.syncCurrentScreen,
    switchScreen: ScreenState.switchScreen,
    importOtherScreen: ScreenState.importOtherScreen,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorState = api;
})(typeof window !== "undefined" ? window : globalThis);
