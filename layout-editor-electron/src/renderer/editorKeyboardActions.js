(function exposeEditorKeyboardActions(globalScope) {
  const MOVE_DELTAS = {
    ArrowLeft: [-1, 0],
    ArrowRight: [1, 0],
    ArrowUp: [0, -1],
    ArrowDown: [0, 1],
  };

  function isEditingTarget(target) {
    const targetTag = String(target?.tagName || "").toLowerCase();
    return targetTag === "input" || targetTag === "select" || targetTag === "textarea";
  }

  function keyboardCommand(event, state) {
    const editingText = isEditingTarget(event.target);
    const commandKey = String(event.key || "").toLowerCase();
    const hasModifier = Boolean(event.ctrlKey || event.metaKey);
    if (!editingText && hasModifier && commandKey === "z") {
      return { type: event.shiftKey ? "redo" : "undo" };
    }
    if (!editingText && hasModifier && commandKey === "y") {
      return { type: "redo" };
    }
    if (!editingText && state.selectedId && hasModifier && commandKey === "d") {
      return { type: "duplicate" };
    }
    if (editingText || !state.selectedId) {
      return { type: "none" };
    }
    if (event.key === "Delete" || event.key === "Backspace") {
      return { type: "delete" };
    }
    const move = MOVE_DELTAS[event.key];
    if (!move) {
      return { type: "none" };
    }
    const step = event.shiftKey ? 10 : 1;
    return { type: "move", dx: move[0] * step, dy: move[1] * step };
  }

  function moveSelectedElement(state, element, command, editor) {
    if (!element || command.type !== "move") {
      return false;
    }
    element.x = Number(element.x || 0) + command.dx;
    element.y = Number(element.y || 0) + command.dy;
    editor.normalizeElementForCanvas(element, state.layout.canvas || {});
    return true;
  }

  const api = {
    isEditingTarget,
    keyboardCommand,
    moveSelectedElement,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorKeyboardActions = api;
})(typeof window !== "undefined" ? window : globalThis);
