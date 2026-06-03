const test = require("node:test");
const assert = require("node:assert/strict");

const CanvasViewModel = require("../src/renderer/editorCanvasViewModel.js");

test("canvas view model hit tests visible elements by z order", () => {
  const elements = [
    { id: "low", x: 0, y: 0, w: 100, h: 100, z: 1 },
    { id: "hidden", x: 0, y: 0, w: 100, h: 100, z: 99, visible: false },
    { id: "top", x: 20, y: 20, w: 40, h: 40, z: 2 },
  ];

  assert.equal(CanvasViewModel.hitTestElement(elements, 30, 30).id, "top");
  assert.equal(CanvasViewModel.hitTestElement(elements, 10, 10).id, "low");
  assert.equal(CanvasViewModel.hitTestElement(elements, 120, 120), undefined);
});

test("canvas view model maps pointer coordinates and stage scale", () => {
  const canvas = { width: 200, height: 100 };
  const stageRect = { left: 10, top: 20, width: 400, height: 200 };

  assert.deepEqual(CanvasViewModel.eventToCanvasPoint({ clientX: 210, clientY: 120 }, canvas, stageRect), {
    x: 100,
    y: 50,
  });
  assert.deepEqual(CanvasViewModel.canvasScale(canvas, stageRect), { sx: 2, sy: 2, width: 400, height: 200 });
});
