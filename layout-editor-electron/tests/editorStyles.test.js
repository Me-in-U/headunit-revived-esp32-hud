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
  "./styles/vehicle-live.css",
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
    "vehicle-live.css": [
      ".tool-tabs",
      ".tool-panel",
      ".connection-layout",
      ".can-analysis-layout",
      ".live-log-panel",
      ".obd-device-list",
      ".com-port-list",
      ".advanced-settings",
      ".obd-section",
      ".analysis-list",
    ],
    "canvas.css": [".canvas-panel", ".canvas-panel.is-collapsed", ".preview-frame", ".preview-stage", ".element-hitbox"],
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

test("vehicle live controls use left-aligned rows instead of split floating controls", () => {
  const content = fs.readFileSync(path.join(rendererDir, "styles", "vehicle-live.css"), "utf8");

  assert.match(content, /\.section-title\s*{[^}]*display:\s*grid;/s);
  assert.match(content, /\.check-row\s*{[^}]*justify-content:\s*flex-start;/s);
  assert.match(content, /\.check-row\s*{[^}]*width:\s*fit-content;/s);
  assert.match(content, /\.button-row\s*{[^}]*justify-content:\s*flex-start;/s);
  assert.doesNotMatch(content, /\.button-row\s*{[^}]*justify-content:\s*space-between;/s);
});

test("connection panel is split evenly while CAN analysis keeps a 7:3 desktop structure", () => {
  const content = fs.readFileSync(path.join(rendererDir, "styles", "vehicle-live.css"), "utf8");

  assert.match(content, /\.connection-layout\s*{[^}]*display:\s*grid;[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+minmax\(0,\s*1fr\);/s);
  assert.match(content, /\.can-analysis-layout\s*{[^}]*display:\s*grid;[^}]*grid-template-columns:\s*minmax\(0,\s*7fr\)\s+minmax\(0,\s*3fr\);/s);
  assert.match(content, /\.connection-button-row\s*{[^}]*display:\s*grid;/s);
  assert.match(content, /\.live-log-panel\s*{[^}]*display:\s*grid;/s);
  assert.match(content, /@media\s*\(max-width:\s*900px\)[\s\S]*\.connection-layout,[\s\S]*\.can-analysis-layout\s*{[^}]*grid-template-columns:\s*1fr;/s);
});

test("OBD decoded value table expands without its own scrollbar", () => {
  const content = fs.readFileSync(path.join(rendererDir, "styles", "vehicle-live.css"), "utf8");

  assert.match(content, /\.obd-section\s*{[^}]*display:\s*grid;[^}]*overflow:\s*visible;/s);
  assert.match(content, /\.obd-value-list\s*{[^}]*display:\s*block;[^}]*max-height:\s*none;[^}]*overflow:\s*visible;/s);
  assert.match(content, /\.obd-value-table\s*{[^}]*overflow:\s*visible;/s);
  assert.match(content, /\.obd-raw-section\s*{[^}]*border-top:/s);
  assert.match(content, /\.obd-raw-list\s*{[^}]*max-height:\s*180px;[^}]*overflow:\s*auto;/s);
});

test("raw analysis rows wrap long OBD responses instead of overlapping", () => {
  const content = fs.readFileSync(path.join(rendererDir, "styles", "vehicle-live.css"), "utf8");

  assert.match(content, /\.analysis-list\s*{[^}]*min-width:\s*0;/s);
  assert.match(content, /\.analysis-row\s*{[^}]*overflow-wrap:\s*anywhere;[^}]*white-space:\s*pre-wrap;[^}]*word-break:\s*break-word;/s);
});

test("canvas panel can collapse so tools have more vertical space", () => {
  const content = fs.readFileSync(path.join(rendererDir, "styles", "canvas.css"), "utf8");

  assert.match(content, /\.canvas-panel\.is-collapsed\s*{[^}]*grid-template-rows:\s*auto;/s);
  assert.match(content, /\.canvas-panel\.is-collapsed\s+\.preview-frame,[\s\S]*\.canvas-panel\.is-collapsed\s+\.statusbar\s*{[^}]*display:\s*none;/s);
});
