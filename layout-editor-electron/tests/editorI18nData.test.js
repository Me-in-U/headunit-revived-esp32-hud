const test = require("node:test");
const assert = require("node:assert/strict");

const I18nData = require("../src/renderer/editorI18nData.js");

test("i18n data exposes supported languages app copy and inspector labels", () => {
  assert.equal(I18nData.APP_LANGUAGE_KEY, "headunitHudEditorLanguage");
  assert.deepEqual(I18nData.APP_LANGUAGES, ["ko", "en"]);
  assert.equal(I18nData.I18N.ko.save, "저장");
  assert.equal(I18nData.I18N.en.save, "Save");
  assert.equal(I18nData.PROPERTY_LABELS_KO.value_style, "값 스타일");
  assert.equal(I18nData.SECTION_LABELS_KO.layout, "위치/크기");
});
