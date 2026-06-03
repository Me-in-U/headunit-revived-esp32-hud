(function exposeEditorFileCommands(globalScope) {
  async function openLayoutCommand(state, service, deps) {
    if (!deps.confirmDiscardChanges()) {
      return { opened: false, canceled: true };
    }
    const response = await service.openLayout();
    if (!applyLoadedLayoutCommand(state, response, deps)) {
      return { opened: false };
    }
    deps.renderAll();
    await deps.renderPreview();
    return { opened: true };
  }

  async function resetDefaultLayoutCommand(state, service, deps) {
    const message = state.dirty
      ? `${deps.translate("unsaved")}. ${deps.translate("resetConfirm")}`
      : deps.translate("resetConfirm");
    if (!deps.confirm(message)) {
      return { reset: false, canceled: true };
    }
    const response = await service.loadDefault();
    if (!applyLoadedLayoutCommand(state, response, deps)) {
      return { reset: false };
    }
    deps.renderAll();
    await deps.renderPreview();
    deps.setStatus(deps.translate("resetReady"), "ok");
    return { reset: true };
  }

  async function saveLayoutCommand(state, saveAs, service, deps) {
    try {
      const result = await deps.fileActions.saveLayout(state, saveAs, service);
      if (result.canceled) {
        return { saved: false, canceled: true };
      }
      if (!result.saved) {
        deps.setStatus(result.errorMessage, "error");
        return result;
      }
      deps.renderAll();
      deps.setStatus(result.message, "ok");
      return result;
    } catch (error) {
      deps.setStatus(error.message, "error");
      return { saved: false, errorMessage: error.message };
    }
  }

  async function validateLayoutCommand(state, service, deps) {
    try {
      const response = await deps.fileActions.validateLayout(state, service);
      if (response.ok) {
        deps.hideValidationDrawer();
        deps.setStatus(`Layout OK · ${response.nonBackgroundPixels} non-background pixels`, "ok");
        deps.pixelStatus.textContent = response.renderSize.join(" x ");
        return { validated: true, ok: true };
      }
      deps.showValidationDrawer(response.errors);
      deps.setStatus(response.errors.join("\n"), "error");
      return { validated: true, ok: false, errors: response.errors };
    } catch (error) {
      deps.setStatus(error.message, "error");
      return { validated: false, errorMessage: error.message };
    }
  }

  async function exportSnapshotCommand(state, service, deps) {
    return exportCommand(state, service, deps.fileActions.exportSnapshot, deps);
  }

  async function exportFieldPackCommand(state, service, deps) {
    return exportCommand(state, service, deps.fileActions.exportFieldPack, deps);
  }

  async function exportCommand(state, service, action, deps) {
    const result = await action(state, service);
    if (result.canceled) {
      return result;
    }
    if (result.ok) {
      deps.setStatus(result.message, "ok");
    } else {
      deps.setStatus(result.errorMessage, "error");
    }
    return result;
  }

  function applyLoadedLayoutCommand(state, response, deps) {
    const result = deps.fileActions.applyLoadedLayout(state, response, deps.editor);
    if (result.errorMessage) {
      deps.setStatus(result.errorMessage, "error");
      return false;
    }
    if (!result.applied) {
      return false;
    }
    deps.hideDragGhost();
    deps.hideValidationDrawer();
    return true;
  }

  const api = {
    applyLoadedLayoutCommand,
    exportFieldPackCommand,
    exportSnapshotCommand,
    openLayoutCommand,
    resetDefaultLayoutCommand,
    saveLayoutCommand,
    validateLayoutCommand,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorFileCommands = api;
})(typeof window !== "undefined" ? window : globalThis);
