(function exposeEditorPaletteGroups(globalScope) {
  const Keys =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorPaletteKeys.js")
      : globalScope.EditorPaletteKeys;

  function cleanFamilyLabel(item) {
    const label = String(item.label || item.binding || item.icon || item.type || "Element").trim();
    const variant = Keys.elementVariant(item).replace(/_/g, " ");
    if (String(item.type || "value") === "value") {
      return label.replace(new RegExp(`\\s+${escapeRegExp(variant)}$`, "i"), "") || label;
    }
    if (String(item.type || "value") === "gear_indicator") {
      return label.replace(/\s+(strip|active|active only)$/i, "") || label;
    }
    return label;
  }

  function variantLabel(value) {
    return titleCase(String(value || "default"));
  }

  function groupPaletteFamilies(items, category) {
    const groups = [];
    const byKey = new Map();
    for (const item of items || []) {
      const familyKey = Keys.elementFamilyKey(item);
      if (!byKey.has(familyKey)) {
        const group = {
          category,
          familyKey,
          label: cleanFamilyLabel(item),
          type: String(item.type || "value"),
          binding: item.binding || "",
          variants: [],
        };
        byKey.set(familyKey, group);
        groups.push(group);
      }
      const variant = Keys.elementVariant(item);
      byKey.get(familyKey).variants.push({
        variant,
        label: variantLabel(variant),
        paletteKey: Keys.paletteKey(item, category),
        item,
      });
    }
    return groups;
  }

  function titleCase(value) {
    return String(value || "")
      .replace(/[_-]+/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function escapeRegExp(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  const api = {
    cleanFamilyLabel,
    groupPaletteFamilies,
    variantLabel,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorPaletteGroups = api;
})(typeof window !== "undefined" ? window : globalThis);
