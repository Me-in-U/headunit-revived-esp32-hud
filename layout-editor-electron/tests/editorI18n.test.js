const test = require("node:test");
const assert = require("node:assert/strict");

const I18n = require("../src/renderer/editorI18n.js");

test("normalizeLanguage keeps supported languages and defaults to Korean", () => {
  assert.equal(I18n.normalizeLanguage("en"), "en");
  assert.equal(I18n.normalizeLanguage("ko"), "ko");
  assert.equal(I18n.normalizeLanguage("fr"), "ko");
  assert.equal(I18n.normalizeLanguage(null), "ko");
});

test("translate returns localized app copy and defaults unsupported languages to Korean", () => {
  assert.equal(I18n.translate("ko", "save"), "저장");
  assert.equal(I18n.translate("en", "save"), "Save");
  assert.equal(I18n.translate("fr", "save"), "저장");
  assert.equal(I18n.translate("ko", "missing_key"), "missing_key");
});

test("propertyLabel localizes known fields only in Korean", () => {
  assert.equal(I18n.propertyLabel("ko", "value_style", "Value style"), "값 스타일");
  assert.equal(I18n.propertyLabel("en", "value_style", "Value style"), "Value style");
  assert.equal(I18n.propertyLabel("ko", "unknown", "Unknown"), "Unknown");
});

test("sectionLabel localizes inspector section headings", () => {
  assert.equal(I18n.sectionLabel("ko", { id: "layout", label: "Position / Size" }), "위치/크기");
  assert.equal(I18n.sectionLabel("en", { id: "layout", label: "Position / Size" }), "Position / Size");
  assert.equal(I18n.sectionLabel("ko", { id: "custom", label: "Custom" }), "Custom");
});
