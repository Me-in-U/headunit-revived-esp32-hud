(function exposeEditorCanvasViewModel(globalScope) {
  function hitTestElement(elements, x, y) {
    return [...(elements || [])]
      .filter((element) => element.visible !== false)
      .sort((left, right) => Number(right.z || 0) - Number(left.z || 0))
      .find(
        (element) =>
          x >= Number(element.x || 0) &&
          x <= Number(element.x || 0) + Number(element.w || 0) &&
          y >= Number(element.y || 0) &&
          y <= Number(element.y || 0) + Number(element.h || 0)
      );
  }

  function eventToCanvasPoint(event, canvas, stageRect) {
    const canvasWidth = numberOrDefault(canvas?.width || 1920, 1920);
    const canvasHeight = numberOrDefault(canvas?.height || 480, 480);
    return {
      x: Math.round(((event.clientX - stageRect.left) / stageRect.width) * canvasWidth),
      y: Math.round(((event.clientY - stageRect.top) / stageRect.height) * canvasHeight),
    };
  }

  function canvasScale(canvas, stageRect) {
    const canvasWidth = numberOrDefault(canvas?.width || 1920, 1920);
    const canvasHeight = numberOrDefault(canvas?.height || 480, 480);
    return {
      sx: stageRect.width / canvasWidth,
      sy: stageRect.height / canvasHeight,
      width: stageRect.width,
      height: stageRect.height,
    };
  }

  function numberOrDefault(value, fallback) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }

  const api = {
    canvasScale,
    eventToCanvasPoint,
    hitTestElement,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorCanvasViewModel = api;
})(typeof window !== "undefined" ? window : globalThis);
