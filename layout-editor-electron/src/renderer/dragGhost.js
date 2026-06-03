(function exposeDragGhost(globalScope) {
  function computeDragGhostStyle(element, canvas, stageSize) {
    const canvasWidth = positiveNumber(canvas?.width, 1920);
    const canvasHeight = positiveNumber(canvas?.height, 480);
    const stageWidth = positiveNumber(stageSize?.width, canvasWidth);
    const stageHeight = positiveNumber(stageSize?.height, canvasHeight);
    const sx = stageWidth / canvasWidth;
    const sy = stageHeight / canvasHeight;
    const x = numberOrDefault(element?.x, 0);
    const y = numberOrDefault(element?.y, 0);
    const w = Math.max(1, numberOrDefault(element?.w, 1));
    const h = Math.max(1, numberOrDefault(element?.h, 1));
    return {
      left: `${x * sx}px`,
      top: `${y * sy}px`,
      width: `${w * sx}px`,
      height: `${h * sy}px`,
      backgroundSize: `${stageWidth}px ${stageHeight}px`,
      backgroundPosition: `${-x * sx}px ${-y * sy}px`,
    };
  }

  function numberOrDefault(value, fallback) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }

  function positiveNumber(value, fallback) {
    return Math.max(1, numberOrDefault(value, fallback));
  }

  const api = { computeDragGhostStyle };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.DragGhost = api;
})(typeof window !== "undefined" ? window : globalThis);
