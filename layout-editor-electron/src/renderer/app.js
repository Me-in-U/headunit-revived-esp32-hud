const AppRuntime = window.EditorAppRuntime;
const Modules = AppRuntime.collectWindowModules(window);

const state = Modules.appState.createInitialState(Modules.i18n, localStorage);
const dom = Modules.appState.createEditorDom();
const refs = {
  clearTimeoutRef: clearTimeout,
  documentRef: document,
  dom,
  localStorageRef: localStorage,
  navigatorRef: navigator,
  requestAnimationFrameRef: requestAnimationFrame,
  setTimeoutRef: setTimeout,
  windowRef: window,
};
const handlers = Modules.appHandlers.createAppHandlers({
  state,
  dom,
  modules: Modules,
  refs,
  runtimeFactory: appRuntime,
});

document.addEventListener("DOMContentLoaded", init);

async function init() {
  await Modules.appBootstrap.initializeEditor(state, dom, Modules.appDeps.appBootstrapDeps(appRuntime()));
}

function appRuntime() {
  return AppRuntime.createAppRuntime({
    modules: Modules,
    refs,
    handlers,
  });
}
