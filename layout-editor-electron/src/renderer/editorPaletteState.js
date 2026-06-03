(function exposeEditorPaletteState(globalScope) {
  const Identity =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorPaletteIdentity.js")
      : globalScope.EditorPaletteIdentity;
  const Elements =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorPaletteElementState.js")
      : globalScope.EditorPaletteElementState;

  const api = {
    DEFAULT_GEARS: Elements.DEFAULT_GEARS,
    clone: Identity.clone,
    paletteKey: Identity.paletteKey,
    elementFamilyKey: Identity.elementFamilyKey,
    elementVariant: Identity.elementVariant,
    elementPaletteKey: Identity.elementPaletteKey,
    elementPaletteKeys: Identity.elementPaletteKeys,
    paletteTemplateMatchesElement: Identity.paletteTemplateMatchesElement,
    paletteTemplateMatchesFamily: Identity.paletteTemplateMatchesFamily,
    findPaletteElement: Elements.findPaletteElement,
    findPaletteFamilyElement: Elements.findPaletteFamilyElement,
    groupPaletteFamilies: Identity.groupPaletteFamilies,
    uniqueId: Elements.uniqueId,
    nextZ: Elements.nextZ,
    normalizeElementForCanvas: Elements.normalizeElementForCanvas,
    createElement: Elements.createElement,
    addOrTogglePaletteElement: Elements.addOrTogglePaletteElement,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPaletteState = api;
})(typeof window !== "undefined" ? window : globalThis);
