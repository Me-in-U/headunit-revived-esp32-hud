const test = require("node:test");
const assert = require("node:assert/strict");

const { computeDragGhostStyle } = require("../src/renderer/dragGhost.js");

test("drag ghost crops the current preview image to the moved element bounds", () => {
  const style = computeDragGhostStyle(
    { x: 480, y: 120, w: 240, h: 80 },
    { width: 1920, height: 480 },
    { width: 960, height: 240 }
  );

  assert.deepEqual(style, {
    left: "240px",
    top: "60px",
    width: "120px",
    height: "40px",
    backgroundSize: "960px 240px",
    backgroundPosition: "-240px -60px",
  });
});

test("drag ghost keeps a visible crop for tiny or invalid element dimensions", () => {
  const style = computeDragGhostStyle(
    { x: 10, y: 20, w: 0, h: "bad" },
    { width: 100, height: 50 },
    { width: 200, height: 100 }
  );

  assert.equal(style.width, "2px");
  assert.equal(style.height, "2px");
  assert.equal(style.backgroundPosition, "-20px -40px");
});
