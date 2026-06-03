(function exposeEditorDomActions(globalScope) {
  function showValidationDrawer(state, dom, messages, documentRef) {
    state.validationMessages = messages || [];
    dom.validationMessages.replaceChildren();
    for (const message of state.validationMessages) {
      const item = documentRef.createElement("div");
      item.className = "validation-message";
      item.textContent = message;
      dom.validationMessages.append(item);
    }
    dom.validationDrawer.hidden = false;
  }

  function hideValidationDrawer(state, dom) {
    if (!dom.validationDrawer) {
      return false;
    }
    state.validationMessages = [];
    dom.validationDrawer.hidden = true;
    dom.validationMessages?.replaceChildren();
    return true;
  }

  function updateFilePath(state, dom, translate) {
    const marker = state.dirty ? ` · ${translate("unsaved")}` : "";
    dom.filePath.textContent = `${state.path || "Untitled layout"}${marker}`;
    dom.filePath.classList.toggle("dirty", state.dirty);
  }

  function setStatus(dom, message, kind = "") {
    dom.statusText.textContent = message;
    dom.statusText.parentElement.classList.toggle("ok", kind === "ok");
    dom.statusText.parentElement.classList.toggle("error", kind === "error");
  }

  function applyLanguage(documentRef, language, translate) {
    documentRef.documentElement.lang = language;
    for (const node of documentRef.querySelectorAll("[data-i18n]")) {
      node.textContent = translate(node.dataset.i18n);
    }
    for (const node of documentRef.querySelectorAll("[data-i18n-placeholder]")) {
      node.placeholder = translate(node.dataset.i18nPlaceholder);
    }
  }

  const api = {
    applyLanguage,
    hideValidationDrawer,
    setStatus,
    showValidationDrawer,
    updateFilePath,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorDomActions = api;
})(typeof window !== "undefined" ? window : globalThis);
