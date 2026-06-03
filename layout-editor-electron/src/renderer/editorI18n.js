(function exposeEditorI18n(globalScope) {
  const Data =
    typeof require !== "undefined" && typeof module !== "undefined" && module.exports
      ? require("./editorI18nData.js")
      : globalScope.EditorI18nData;

  function normalizeLanguage(language) {
    return Data.APP_LANGUAGES.includes(language) ? language : "ko";
  }

  function translate(language, key) {
    const normalized = normalizeLanguage(language);
    return Data.I18N[normalized]?.[key] || Data.I18N.en[key] || key;
  }

  function propertyLabel(language, key, fallback) {
    if (normalizeLanguage(language) === "ko") {
      return Data.PROPERTY_LABELS_KO[key] || fallback;
    }
    return fallback;
  }

  function sectionLabel(language, section) {
    if (normalizeLanguage(language) === "ko") {
      return Data.SECTION_LABELS_KO[section.id] || section.label;
    }
    return section.label;
  }

  const api = {
    APP_LANGUAGE_KEY: Data.APP_LANGUAGE_KEY,
    APP_LANGUAGES: Data.APP_LANGUAGES,
    normalizeLanguage,
    propertyLabel,
    sectionLabel,
    translate,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorI18n = api;
})(typeof window !== "undefined" ? window : globalThis);
