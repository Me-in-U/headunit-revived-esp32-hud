(function exposeEditorBrowserRefs(globalScope) {
  function createBrowserRefs({ documentRef, dom, localStorageRef, navigatorRef, windowRef }) {
    return {
      clearTimeoutRef: (timer) => windowRef.clearTimeout(timer),
      documentRef,
      dom,
      localStorageRef,
      navigatorRef,
      requestAnimationFrameRef: (callback) => windowRef.requestAnimationFrame(callback),
      setTimeoutRef: (callback, delay) => windowRef.setTimeout(callback, delay),
      windowRef,
    };
  }

  const api = {
    createBrowserRefs,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  globalScope.EditorBrowserRefs = api;
})(typeof window !== "undefined" ? window : globalThis);
