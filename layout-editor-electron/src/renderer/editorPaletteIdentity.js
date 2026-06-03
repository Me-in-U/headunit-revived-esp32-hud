(function exposeEditorPaletteIdentity(globalScope) {
  const Keys =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorPaletteKeys.js")
      : globalScope.EditorPaletteKeys;
  const Groups =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorPaletteGroups.js")
      : globalScope.EditorPaletteGroups;

  const api = {
    cleanFamilyLabel: Groups.cleanFamilyLabel,
    clone: Keys.clone,
    elementFamilyKey: Keys.elementFamilyKey,
    elementPaletteKey: Keys.elementPaletteKey,
    elementPaletteKeys: Keys.elementPaletteKeys,
    elementVariant: Keys.elementVariant,
    groupPaletteFamilies: Groups.groupPaletteFamilies,
    paletteKey: Keys.paletteKey,
    paletteTemplateMatchesElement: Keys.paletteTemplateMatchesElement,
    paletteTemplateMatchesFamily: Keys.paletteTemplateMatchesFamily,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPaletteIdentity = api;
})(typeof window !== "undefined" ? window : globalThis);
