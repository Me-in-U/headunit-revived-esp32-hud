const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const rendererDir = path.join(__dirname, "..", "src", "renderer");
const stylesPath = path.join(rendererDir, "styles.css");
const expectedImports = [
  "./styles/base.css",
  "./styles/shell.css",
  "./styles/palette.css",
  "./styles/canvas.css",
  "./styles/inspector.css",
];

test("styles.css is a stylesheet manifest for feature css modules", () => {
  const content = fs.readFileSync(stylesPath, "utf8").trim();
  const importLines = content.split(/\r?\n/).filter(Boolean);

  assert.deepEqual(importLines, expectedImports.map((href) => `@import url("${href}");`));
});

test("feature css modules exist and own their expected selectors", () => {
  const expectedSelectors = {
    "base.css": [":root", "body", "button"],
    "shell.css": [".app-shell", ".topbar", ".workspace"],
    "palette.css": [".category-tabs", ".palette-list", ".variant-segment"],
    "canvas.css": [".canvas-panel", ".preview-stage", ".element-hitbox"],
    "inspector.css": [".property-grid", ".validation-drawer", ".layer-row"],
  };

  for (const [fileName, selectors] of Object.entries(expectedSelectors)) {
    const modulePath = path.join(rendererDir, "styles", fileName);
    assert.equal(fs.existsSync(modulePath), true, `${fileName} should exist`);
    const content = fs.readFileSync(modulePath, "utf8");
    assert.match(content, /\S/, `${fileName} should not be empty`);
    for (const selector of selectors) {
      assert.equal(content.includes(selector), true, `${fileName} should include ${selector}`);
    }
  }
});
