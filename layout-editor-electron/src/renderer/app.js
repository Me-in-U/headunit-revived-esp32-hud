const Editor = window.EditorState;
const DragGhost = window.DragGhost;

const PROPERTY_FIELDS = [
  ["id", "ID", "text"],
  ["label", "Label", "text"],
  ["binding", "Binding", "text"],
  ["event_binding", "Event binding", "text"],
  ["side_binding", "Side binding", "text"],
  ["fallback_bindings", "Fallbacks", "text"],
  ["text", "Text", "text"],
  ["x", "X", "number"],
  ["y", "Y", "number"],
  ["w", "W", "number"],
  ["h", "H", "number"],
  ["font_size", "Font size", "number"],
  ["font_family", "Font family", "text"],
  ["font_weight", "Font weight", "select", ["normal", "bold"]],
  ["font_style", "Font style", "select", ["normal", "italic"]],
  ["align", "Align", "select", ["left", "center", "right"]],
  ["value_style", "Value style", "select", ["digital", "bar", "analog", "needle", "sport_gauge"]],
  ["gear_style", "Gear style", "select", ["strip", "active_only"]],
  ["gears", "Gears", "text"],
  ["active_font_size", "Active font", "number"],
  ["min_value", "Minimum value", "number"],
  ["max_value", "Maximum value", "number"],
  ["tick_interval", "Tick interval", "number"],
  ["prefix", "Prefix", "text"],

  ["suffix", "Suffix", "text"],
  ["color", "Color", "color"],
  ["active_color", "Active", "color"],
  ["inactive_color", "Inactive", "color"],
  ["accent", "Accent", "color"],
  ["redline_color", "Redline", "color"],
];

const HANDLE_NAMES = ["nw", "n", "ne", "e", "se", "s", "sw", "w"];
const APP_LANGUAGE_KEY = "headunitHudEditorLanguage";
const APP_LANGUAGES = ["ko", "en"];

const I18N = {
  en: {
    open: "Open",
    save: "Save",
    saveAs: "Save As",
    undo: "Undo",
    redo: "Redo",
    reset: "Reset",
    validate: "Validate",
    fieldPack: "Field Pack",
    vehicle: "Vehicle",
    screen: "Screen",
    importScreen: "Import Other Screen",
    language: "Language",
    background: "Background",
    weather: "Weather",
    bgImage: "BG Image",
    clearBg: "Clear BG",
    elements: "Elements",
    elementsHint: "Add by driver task",
    searchPalette: "Search elements",
    canvasTitle: "1920 x 480 HUD Canvas",
    fit: "Fit",
    duplicate: "Duplicate",
    delete: "Delete",
    inspector: "Inspector",
    bringFront: "Bring front",
    sendBack: "Send back",
    layers: "Layers",
    loading: "Loading Electron editor...",
    renderPreview: "Rendering Pi preview...",
    previewReady: "Preview ready",
    noSelection: "No selection",
    selectElement: "Select an element on the canvas or layer list.",
    noElements: "No elements on this screen.",
    added: "Added",
    resetConfirm: "Load the default layout and discard unsaved editor changes?",
    resetReady: "Default layout loaded",
    duplicateReady: "Element duplicated",
    weatherLoading: "Fetching current weather...",
    weatherReady: "Weather updated",
    validationIssues: "Validation",
    close: "Close",
    noPaletteResults: "No matching elements.",
    unsaved: "Unsaved changes",
    discardConfirm: "Discard unsaved editor changes?",
  },
  ko: {
    open: "열기",
    save: "저장",
    saveAs: "다른 이름 저장",
    undo: "실행 취소",
    redo: "다시 실행",
    reset: "초기화",
    validate: "검증",
    fieldPack: "필드팩",
    vehicle: "차량",
    screen: "화면",
    importScreen: "다른 화면 가져오기",
    language: "언어",
    background: "배경",
    weather: "날씨",
    bgImage: "배경 이미지",
    clearBg: "배경 제거",
    elements: "요소",
    elementsHint: "운전 정보별 추가",
    searchPalette: "요소 검색",
    canvasTitle: "1920 x 480 HUD 캔버스",
    fit: "맞춤",
    duplicate: "복제",
    delete: "삭제",
    inspector: "인스펙터",
    bringFront: "앞으로",
    sendBack: "뒤로",
    layers: "레이어",
    loading: "Electron 편집기 로딩 중...",
    renderPreview: "Pi 미리보기 렌더링 중...",
    previewReady: "미리보기 준비됨",
    noSelection: "선택 없음",
    selectElement: "캔버스나 레이어 목록에서 요소를 선택하세요.",
    noElements: "현재 화면에 요소가 없습니다.",
    added: "추가됨",
    resetConfirm: "기본 레이아웃을 다시 불러오고 저장하지 않은 편집 내용을 버릴까요?",
    resetReady: "기본 레이아웃을 불러왔습니다",
    duplicateReady: "요소를 복제했습니다",
    weatherLoading: "현재 날씨를 가져오는 중...",
    weatherReady: "날씨를 갱신했습니다",
    validationIssues: "검증",
    close: "닫기",
    noPaletteResults: "일치하는 요소가 없습니다.",
    unsaved: "저장되지 않은 변경",
    discardConfirm: "저장하지 않은 편집 내용을 버릴까요?",
  },
};

const PROPERTY_LABELS_KO = {
  id: "ID",
  label: "라벨",
  binding: "바인딩",
  event_binding: "이벤트 바인딩",
  side_binding: "방향 바인딩",
  fallback_bindings: "대체 바인딩",
  text: "텍스트",
  x: "X",
  y: "Y",
  w: "W",
  h: "H",
  font_size: "글자 크기",
  font_family: "글꼴",
  font_weight: "굵기",
  font_style: "스타일",
  align: "정렬",
  value_style: "값 스타일",
  gear_style: "기어 스타일",
  gears: "기어",
  active_font_size: "활성 글자",
  min_value: "최소값",
  max_value: "최대값",
  tick_interval: "눈금 단위",
  prefix: "접두사",

  suffix: "접미어",
  color: "색상",
  active_color: "활성",
  inactive_color: "비활성",
  accent: "강조",
  redline_color: "레드라인",
};

const state = {
  layout: null,
  path: "",
  currentScreen: "standalone",
  metadata: null,
  vehicleProfiles: {},
  selectedId: "",
  activeCategory: "",
  dirty: false,
  renderToken: 0,
  previewBusy: false,
  previewPending: false,
  drag: null,
  paletteQuery: "",
  validationMessages: [],
  history: {
    undo: [],
    redo: [],
    applying: false,
  },
  appLanguage: APP_LANGUAGES.includes(localStorage.getItem(APP_LANGUAGE_KEY))
    ? localStorage.getItem(APP_LANGUAGE_KEY)
    : "ko",
};

const dom = {};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  bindDom();
  bindActions();
  dom.languageSelect.value = state.appLanguage;
  applyLanguage();
  setStatus(t("loading"));
  state.metadata = await window.hudEditor.metadata();
  state.vehicleProfiles = state.metadata.vehicleProfiles || {};
  state.activeCategory = Object.keys(state.metadata.palette || {})[0] || "";
  const loaded = await window.hudEditor.loadDefault();
  applyLoadedLayout(loaded);
  renderAll();
  await renderPreview();
}

function bindDom() {
  for (const id of [
    "filePath",
    "openBtn",
    "saveBtn",
    "saveAsBtn",
    "undoBtn",
    "redoBtn",
    "resetBtn",
    "validateBtn",
    "exportPngBtn",
    "fieldPackBtn",
    "vehicleSelect",
    "screenSelect",
    "importScreenBtn",
    "languageSelect",
    "weatherBtn",
    "backgroundColor",
    "backgroundImageBtn",
    "clearBackgroundBtn",
    "categoryTabs",
    "paletteSearch",
    "paletteButtons",
    "previewFrame",
    "previewStage",
    "previewImage",
    "dragGhost",
    "selectionOverlay",
    "canvasMeta",
    "statusText",
    "pixelStatus",
    "zoomFitBtn",
    "deleteBtn",
    "selectedLabel",
    "propertyForm",
    "validationDrawer",
    "validationCloseBtn",
    "validationMessages",
    "frontBtn",
    "backBtn",
    "duplicateBtn",
    "layerCount",
    "layerList",
  ]) {
    dom[id] = document.getElementById(id);
  }
}

function bindActions() {
  dom.openBtn.addEventListener("click", openLayout);
  dom.saveBtn.addEventListener("click", () => saveLayout(false));
  dom.saveAsBtn.addEventListener("click", () => saveLayout(true));
  dom.undoBtn.addEventListener("click", undo);
  dom.redoBtn.addEventListener("click", redo);
  dom.resetBtn.addEventListener("click", resetDefaultLayout);
  dom.validateBtn.addEventListener("click", validateLayout);
  dom.exportPngBtn.addEventListener("click", exportSnapshot);
  dom.fieldPackBtn.addEventListener("click", exportFieldPack);
  dom.vehicleSelect.addEventListener("change", onVehicleChange);
  dom.screenSelect.addEventListener("change", onScreenChange);
  dom.importScreenBtn.addEventListener("click", importOtherScreen);
  dom.languageSelect.addEventListener("change", onLanguageChange);
  dom.weatherBtn.addEventListener("click", fetchWeather);
  dom.backgroundColor.addEventListener("input", onBackgroundColor);
  dom.backgroundImageBtn.addEventListener("click", chooseBackgroundImage);
  dom.clearBackgroundBtn.addEventListener("click", clearBackgroundImage);
  dom.paletteSearch.addEventListener("input", () => {
    state.paletteQuery = dom.paletteSearch.value.trim().toLowerCase();
    renderPalette();
  });
  dom.validationCloseBtn.addEventListener("click", hideValidationDrawer);
  dom.deleteBtn.addEventListener("click", deleteSelected);
  dom.duplicateBtn.addEventListener("click", duplicateSelected);
  dom.frontBtn.addEventListener("click", () => bumpZ(1));
  dom.backBtn.addEventListener("click", () => bumpZ(-1));
  dom.zoomFitBtn.addEventListener("click", () => renderOverlay());
  dom.selectionOverlay.addEventListener("pointerdown", onPointerDown);
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
  window.addEventListener("resize", () => renderOverlay());
  window.addEventListener("keydown", onKeyDown);
}

function applyLoadedLayout(response) {
  if (!response || response.canceled) {
    return;
  }
  if (!response.ok) {
    setStatus(response.errors?.join("\n") || "Failed to load layout", "error");
    return;
  }
  state.layout = response.layout;
  state.path = response.path || "";
  state.currentScreen = response.currentScreen || Editor.ensureScreens(state.layout, "standalone");
  state.vehicleProfiles = response.vehicleProfiles || state.vehicleProfiles || {};
  Editor.ensureScreens(state.layout, state.currentScreen);
  state.layout.language = state.layout.language || "ko";
  state.layout.supported_languages = ["ko", "en"];
  state.selectedId = "";
  state.dirty = false;
  state.validationMessages = [];
  state.history.undo = [];
  state.history.redo = [];
  hideDragGhost();
  hideValidationDrawer();
}

function renderAll() {
  if (!state.layout) {
    return;
  }
  renderTopControls();
  renderPalette();
  renderProperties();
  renderLayers();
  renderOverlay();
  updateFilePath();
}

function renderTopControls() {
  const canvas = state.layout.canvas || {};
  dom.canvasMeta.textContent = `${canvas.width || 1920} x ${canvas.height || 480}, ${state.layout.elements?.length || 0} elements`;
  dom.screenSelect.value = state.currentScreen;
  dom.languageSelect.value = state.appLanguage;
  dom.backgroundColor.value = validColor(canvas.background) ? canvas.background : "#05080c";
  dom.undoBtn.disabled = !state.history.undo.length;
  dom.redoBtn.disabled = !state.history.redo.length;
  dom.paletteSearch.value = state.paletteQuery;

  const vehicleIds = Object.keys(state.vehicleProfiles || {});
  dom.vehicleSelect.replaceChildren();
  for (const vehicleId of vehicleIds) {
    const option = document.createElement("option");
    option.value = vehicleId;
    option.textContent = vehicleLabel(vehicleId);
    dom.vehicleSelect.append(option);
  }
  const selected = state.layout.selected_vehicle || vehicleIds[0] || "";
  if (selected && !vehicleIds.includes(selected)) {
    const option = document.createElement("option");
    option.value = selected;
    option.textContent = selected;
    dom.vehicleSelect.append(option);
  }
  dom.vehicleSelect.value = selected;
}

function renderPalette() {
  const palette = state.metadata.palette || {};
  const categories = Object.keys(palette);
  if (!categories.includes(state.activeCategory)) {
    state.activeCategory = categories[0] || "";
  }
  dom.categoryTabs.replaceChildren();
  for (const category of categories) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `category-tab${category === state.activeCategory ? " active" : ""}`;
    button.textContent = category;
    button.addEventListener("click", () => {
      state.activeCategory = category;
      renderPalette();
    });
    dom.categoryTabs.append(button);
  }

  const existingByFamily = new Map();
  for (const element of state.layout.elements || []) {
    existingByFamily.set(Editor.elementFamilyKey(element), element);
  }

  dom.paletteButtons.replaceChildren();
  const groups = Editor.groupPaletteFamilies(palette[state.activeCategory] || [], state.activeCategory)
    .filter((group) => paletteGroupMatches(group, state.paletteQuery));
  if (!groups.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = t("noPaletteResults");
    dom.paletteButtons.append(empty);
    return;
  }
  for (const group of groups) {
    const existing = existingByFamily.get(group.familyKey);
    const activeVariant = existing ? Editor.elementVariant(existing) : "";
    const card = document.createElement("div");
    card.className = `palette-family${existing ? " added" : ""}`;

    const header = document.createElement("div");
    header.className = "palette-family-header";
    header.innerHTML = `<div><span>${escapeHtml(group.label)}</span><small>${escapeHtml(group.binding || group.type)}</small></div><small>${existing ? t("added") : group.type}</small>`;
    card.append(header);

    const variants = document.createElement("div");
    variants.className = "variant-segment";
    for (const variant of group.variants) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = activeVariant === variant.variant ? "active" : "";
      button.textContent = variant.label;
      button.addEventListener("click", () => selectPaletteVariant(variant.item, state.activeCategory));
      variants.append(button);
    }
    card.append(variants);
    dom.paletteButtons.append(card);
  }
}

function selectPaletteVariant(item, category) {
  const before = snapshotState();
  const result = Editor.addOrTogglePaletteElement(state.layout, item, category, state.metadata.palette || {});
  state.selectedId = result.element?.id || "";
  if (result.action === "selected") {
    renderAll();
    return;
  }
  pushUndoSnapshot(before);
  state.history.redo = [];
  markDirty();
  renderAll();
  schedulePreview(40);
}

function paletteGroupMatches(group, query) {
  if (!query) {
    return true;
  }
  const haystack = [
    group.label,
    group.type,
    group.binding,
    ...group.variants.map((variant) => `${variant.label} ${variant.variant} ${variant.item?.label || ""}`),
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query);
}

function renderProperties() {
  const element = selectedElement();
  dom.selectedLabel.textContent = element ? elementSummary(element) : t("noSelection");
  dom.propertyForm.replaceChildren();
  if (!element) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = t("selectElement");
    dom.propertyForm.append(empty);
    return;
  }
  const sections = Editor.inspectorSectionsForElement(element);
  for (const section of sections) {
    const sectionNode = section.collapsed ? document.createElement("details") : document.createElement("section");
    sectionNode.className = `property-section ${section.id}`;
    if (section.collapsed) {
      sectionNode.open = false;
      const summary = document.createElement("summary");
      summary.textContent = sectionLabel(section);
      sectionNode.append(summary);
    } else {
      const heading = document.createElement("h3");
      heading.textContent = sectionLabel(section);
      sectionNode.append(heading);
    }
    const grid = document.createElement("div");
    grid.className = "property-section-grid";
    for (const field of section.fields) {
      grid.append(renderPropertyField(element, section, field));
    }
    sectionNode.append(grid);
    dom.propertyForm.append(sectionNode);
  }
}

function renderPropertyField(element, section, field) {
  const key = field.key;
  const type = field.type;
  const wrap = document.createElement("div");
  wrap.className = `property-field${["id", "label", "binding", "text", "fallback_bindings", "gears"].includes(key) ? " wide" : ""}`;
  const fieldLabel = document.createElement("label");
  fieldLabel.textContent = propertyLabel(key, field.label);
  fieldLabel.htmlFor = `prop-${section.id}-${key}`;
  wrap.append(fieldLabel);

  const input = document.createElement(type === "select" || type === "binding-select" ? "select" : "input");
  input.id = `prop-${section.id}-${key}`;
  input.dataset.key = key;
  input.dataset.inputType = type;
  if (type === "select") {
    for (const optionValue of field.options || []) {
      appendOption(input, optionValue, optionLabel(optionValue));
    }
    input.value = String(element[key] || field.options?.[0] || "");
  } else if (type === "binding-select") {
    const current = String(element[key] || "");
    const options = bindingOptions(current);
    for (const optionValue of options) {
      appendOption(input, optionValue, optionValue || "-");
    }
    input.value = current;
  } else {
    input.type = type;
    input.value = propertyValue(element, key, type);
  }
  input.addEventListener(type === "color" ? "input" : "change", onPropertyInput);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      onPropertyInput(event);
    }
  });
  wrap.append(input);
  return wrap;
}

function appendOption(select, value, label) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  select.append(option);
}

function bindingOptions(current = "") {
  const values = new Set();
  for (const items of Object.values(state.metadata?.palette || {})) {
    for (const item of items || []) {
      for (const key of ["binding", "event_binding", "side_binding"]) {
        if (item[key]) {
          values.add(String(item[key]));
        }
      }
      for (const fallback of item.fallback_bindings || []) {
        values.add(String(fallback));
      }
    }
  }
  collectBindingPaths(state.layout?.dummy_data || {}, "", values);
  if (current) {
    values.add(current);
  }
  return [...values].sort((left, right) => left.localeCompare(right));
}

function collectBindingPaths(value, prefix, output) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return;
  }
  for (const [key, child] of Object.entries(value)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (child && typeof child === "object" && !Array.isArray(child)) {
      collectBindingPaths(child, path, output);
    } else {
      output.add(path);
    }
  }
}

function sectionLabel(section) {
  const ko = {
    basic: "기본",
    layout: "위치/크기",
    data: "데이터",
    presentation: "표현",
    advanced: "고급",
  };
  return state.appLanguage === "ko" ? ko[section.id] || section.label : section.label;
}

function optionLabel(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function elementSummary(element) {
  return `${elementLabel(element)} · ${elementStyleLabel(element)}`;
}

function elementLabel(element) {
  return String(element.label || element.id || element.type || "Element");
}

function elementStyleLabel(element) {
  if (element.type === "value") {
    return optionLabel(element.value_style || "digital");
  }
  if (element.type === "gear_indicator") {
    return optionLabel(element.gear_style || "strip");
  }
  if (element.type === "warning_icon") {
    return "Warning";
  }
  if (element.type === "nav_icon") {
    return "Nav icon";
  }
  return optionLabel(element.type || "value");
}

function elementDataLabel(element) {
  return String(element.binding || element.event_binding || element.icon || element.text || element.id || "");
}

function renderLayers() {
  const elements = [...(state.layout.elements || [])].sort((left, right) => Number(right.z || 0) - Number(left.z || 0));
  dom.layerCount.textContent = String(elements.length);
  dom.layerList.replaceChildren();
  if (!elements.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = t("noElements");
    dom.layerList.append(empty);
    return;
  }
  for (const element of elements) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = `layer-row${element.id === state.selectedId ? " selected" : ""}`;
    row.innerHTML = `<div><div class="layer-id">${escapeHtml(elementLabel(element))}</div><div class="layer-type">${escapeHtml(elementStyleLabel(element))} · ${escapeHtml(elementDataLabel(element))}</div></div><div class="layer-type">z ${Number(element.z || 0)}</div>`;
    row.addEventListener("click", () => {
      state.selectedId = element.id;
      renderAll();
    });
    dom.layerList.append(row);
  }
}

function renderOverlay() {
  if (!state.layout) {
    return;
  }
  const canvas = state.layout.canvas || { width: 1920, height: 480 };
  const { sx, sy } = canvasScale();
  dom.selectionOverlay.replaceChildren();

  for (const element of state.layout.elements || []) {
    if (element.visible === false) {
      continue;
    }
    const box = document.createElement("div");
    box.className = `element-hitbox${element.id === state.selectedId ? " selected" : ""}`;
    box.dataset.id = element.id;
    box.style.left = `${Number(element.x || 0) * sx}px`;
    box.style.top = `${Number(element.y || 0) * sy}px`;
    box.style.width = `${Math.max(1, Number(element.w || 1) * sx)}px`;
    box.style.height = `${Math.max(1, Number(element.h || 1) * sy)}px`;
    if (element.id === state.selectedId) {
      const label = document.createElement("div");
      label.className = "element-label";
      label.textContent = element.id;
      box.append(label);
      for (const handle of HANDLE_NAMES) {
        const grip = document.createElement("div");
        grip.className = `resize-handle ${handle}`;
        grip.dataset.handle = handle;
        grip.style.left = handle.includes("w") ? "-5px" : handle.includes("e") ? "calc(100% - 4px)" : "calc(50% - 4px)";
        grip.style.top = handle.includes("n") ? "-5px" : handle.includes("s") ? "calc(100% - 4px)" : "calc(50% - 4px)";
        box.append(grip);
      }
    }
    dom.selectionOverlay.append(box);
  }
}

async function renderPreview() {
  if (!state.layout) {
    return;
  }
  if (state.previewBusy) {
    state.previewPending = true;
    return;
  }
  state.previewBusy = true;
  const token = ++state.renderToken;
  setStatus(t("renderPreview"));
  try {
    const canvas = state.layout.canvas || {};
    const response = await window.hudEditor.renderPreview({
      layout: state.layout,
      currentScreen: state.currentScreen,
      width: canvas.width || 1920,
      height: canvas.height || 480,
    });
    if (token !== state.renderToken) {
      return;
    }
    dom.previewImage.src = `data:image/png;base64,${response.png}`;
    dom.pixelStatus.textContent = `${response.width} x ${response.height}`;
    hideDragGhost();
    setStatus(t("previewReady"), "ok");
    requestAnimationFrame(renderOverlay);
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    state.previewBusy = false;
    if (state.previewPending) {
      state.previewPending = false;
      schedulePreview(30);
    }
  }
}

function schedulePreview(delay = 100) {
  clearTimeout(schedulePreview.timer);
  schedulePreview.timer = setTimeout(renderPreview, delay);
}

async function openLayout() {
  if (!confirmDiscardChanges()) {
    return;
  }
  const response = await window.hudEditor.openLayout();
  applyLoadedLayout(response);
  renderAll();
  await renderPreview();
}

async function resetDefaultLayout() {
  const message = state.dirty ? `${t("unsaved")}. ${t("resetConfirm")}` : t("resetConfirm");
  if (!window.confirm(message)) {
    return;
  }
  const response = await window.hudEditor.loadDefault();
  applyLoadedLayout(response);
  renderAll();
  await renderPreview();
  setStatus(t("resetReady"), "ok");
}

async function saveLayout(saveAs) {
  try {
    const response = saveAs
      ? await window.hudEditor.saveLayoutAs({ layout: state.layout, path: state.path, currentScreen: state.currentScreen })
      : await window.hudEditor.saveLayout({ layout: state.layout, path: state.path, currentScreen: state.currentScreen });
    if (response.canceled) {
      return;
    }
    if (!response.ok) {
      setStatus(response.errors?.join("\n") || "Save failed", "error");
      return;
    }
    state.layout = response.layout;
    state.path = response.path;
    state.dirty = false;
    state.history.undo = [];
    state.history.redo = [];
    renderAll();
    setStatus(response.message || "Saved", "ok");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

function duplicateSelected() {
  const element = selectedElement();
  if (!element) {
    return;
  }
  recordHistory();
  const copy = Editor.clone(element);
  copy.id = Editor.uniqueId(state.layout, `${element.id}_copy`);
  copy.label = copy.label ? `${copy.label} copy` : copy.id;
  copy.x = Number(copy.x || 0) + 24;
  copy.y = Number(copy.y || 0) + 24;
  copy.z = Editor.nextZ(state.layout);
  Editor.normalizeElementForCanvas(copy, state.layout.canvas || {});
  state.layout.elements = [...(state.layout.elements || []), copy];
  state.selectedId = copy.id;
  markDirty();
  renderAll();
  schedulePreview(40);
  setStatus(t("duplicateReady"), "ok");
}

async function validateLayout() {
  try {
    const response = await window.hudEditor.validateLayout({
      layout: state.layout,
      currentScreen: state.currentScreen,
    });
    if (response.ok) {
      hideValidationDrawer();
      setStatus(`Layout OK · ${response.nonBackgroundPixels} non-background pixels`, "ok");
      dom.pixelStatus.textContent = response.renderSize.join(" x ");
    } else {
      showValidationDrawer(response.errors);
      setStatus(response.errors.join("\n"), "error");
    }
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function exportSnapshot() {
  const response = await window.hudEditor.exportSnapshot({
    layout: state.layout,
    path: state.path,
    currentScreen: state.currentScreen,
  });
  if (response?.canceled) {
    return;
  }
  if (response.ok) {
    setStatus(`PNG exported: ${response.output}`, "ok");
  } else {
    setStatus(response.errors.join("\n"), "error");
  }
}

async function exportFieldPack() {
  const response = await window.hudEditor.exportFieldPack({
    layout: state.layout,
    path: state.path,
    currentScreen: state.currentScreen,
  });
  if (response?.canceled) {
    return;
  }
  if (response.ok) {
    setStatus(`Field pack exported: ${response.output}`, "ok");
  } else {
    setStatus(response.errors.join("\n"), "error");
  }
}

async function fetchWeather() {
  setStatus(t("weatherLoading"));
  try {
    const browserLocation = await requestBrowserLocation();
    const response = await window.hudEditor.fetchWeather({
      layout: state.layout,
      browserLocation,
    });
    if (!response.ok) {
      setStatus(response.errors?.join("\n") || "Weather fetch failed", "error");
      return;
    }
    recordHistory();
    state.layout.dummy_data = state.layout.dummy_data || {};
    state.layout.dummy_data.weather = response.weather;
    markDirty();
    renderAll();
    schedulePreview(30);
    const temp = Number(response.weather?.temp_c);
    const tempText = Number.isFinite(temp) ? `${Math.round(temp)}°C` : "";
    setStatus(`${t("weatherReady")}${tempText ? ` · ${tempText}` : ""} · ${response.location?.source || ""}`, "ok");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

function requestBrowserLocation() {
  if (!navigator.geolocation) {
    return Promise.resolve(null);
  }
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          source: "browser",
        });
      },
      () => resolve(null),
      {
        enableHighAccuracy: true,
        maximumAge: 60_000,
        timeout: 3_500,
      }
    );
  });
}

function onVehicleChange() {
  recordHistory();
  const selected = dom.vehicleSelect.value;
  state.layout.selected_vehicle = selected;
  const profile = state.vehicleProfiles[selected];
  if (profile) {
    const vehicles = Array.isArray(state.layout.vehicles) ? state.layout.vehicles.filter((item) => item.id !== selected) : [];
    vehicles.push(Editor.clone(profile));
    state.layout.vehicles = vehicles.sort((left, right) => String(left.id).localeCompare(String(right.id)));
  }
  markDirty();
}

function onScreenChange() {
  state.currentScreen = Editor.switchScreen(state.layout, state.currentScreen, dom.screenSelect.value);
  state.selectedId = "";
  renderAll();
  schedulePreview(40);
}

function importOtherScreen() {
  recordHistory();
  Editor.importOtherScreen(state.layout, state.currentScreen);
  state.selectedId = "";
  markDirty();
  renderAll();
  schedulePreview(40);
}

function onLanguageChange() {
  state.appLanguage = APP_LANGUAGES.includes(dom.languageSelect.value) ? dom.languageSelect.value : "ko";
  localStorage.setItem(APP_LANGUAGE_KEY, state.appLanguage);
  applyLanguage();
  renderAll();
}

function onBackgroundColor() {
  recordHistory();
  state.layout.canvas = state.layout.canvas || {};
  state.layout.canvas.background = dom.backgroundColor.value;
  markDirty();
  schedulePreview(40);
}

async function chooseBackgroundImage() {
  const response = await window.hudEditor.chooseBackgroundImage();
  if (response.canceled) {
    return;
  }
  recordHistory();
  state.layout.canvas = state.layout.canvas || {};
  state.layout.canvas.background_image = response.dataUrl;
  state.layout.canvas.background_image_name = response.name;
  state.layout.canvas.background_image_fit = "cover";
  markDirty();
  schedulePreview(40);
}

function clearBackgroundImage() {
  recordHistory();
  const canvas = state.layout.canvas || {};
  delete canvas.background_image;
  delete canvas.background_image_name;
  delete canvas.background_image_fit;
  markDirty();
  schedulePreview(40);
}

function onPropertyInput(event) {
  const element = selectedElement();
  if (!element) {
    return;
  }
  recordHistory();
  const propertyScrollTop = dom.propertyForm.scrollTop;
  const key = event.currentTarget.dataset.key;
  let value = event.currentTarget.value;
  if (key === "id" && value && value !== element.id) {
    value = Editor.uniqueId(state.layout, value, element.id);
    element.id = value;
    state.selectedId = value;
    event.currentTarget.value = value;
  } else if (["x", "y", "w", "h", "font_size", "active_font_size"].includes(key)) {
    if (value !== "") {
      element[key] = Number.parseInt(value, 10);
    }
  } else if (["min_value", "max_value", "tick_interval"].includes(key)) {
    if (element.type === "value") {
      if (value === "") {
        delete element[key];
      } else {
        const number = Number.parseFloat(value);
        if (Number.isFinite(number)) {
          element[key] = Number.isInteger(number) ? Number.parseInt(value, 10) : number;
        }
      }
    }
  } else if (key === "fallback_bindings") {
    element[key] = value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  } else if (key === "gears") {
    element[key] = value
      .replace(/\//g, ",")
      .split(",")
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean);
  } else if (key === "value_style") {
    if (element.type === "value") {
      element[key] = value;
      delete element.palette_key;
    }
  } else if (key === "gear_style") {
    if (element.type === "gear_indicator") {
      element[key] = value;
      delete element.palette_key;
    }
  } else if (Editor.COLOR_KEYS.includes(key)) {
    if (value) {
      element[key] = value.toLowerCase();
    }
  } else {
    element[key] = value;
    if (["binding", "event_binding", "side_binding", "icon"].includes(key)) {
      delete element.palette_key;
    }
  }
  Editor.normalizeElementForCanvas(element, state.layout.canvas || {});
  markDirty();
  renderProperties();
  requestAnimationFrame(() => {
    dom.propertyForm.scrollTop = propertyScrollTop;
  });
  renderLayers();
  renderOverlay();
  schedulePreview(60);
}

function onPointerDown(event) {
  if (!state.layout) {
    return;
  }
  const point = eventToCanvas(event);
  const handle = event.target?.dataset?.handle || "";
  const targetBox = event.target.closest?.(".element-hitbox");
  const element = handle && targetBox ? elementById(targetBox.dataset.id) : targetBox ? elementById(targetBox.dataset.id) : hitTest(point.x, point.y);
  if (!element) {
    state.selectedId = "";
    hideDragGhost();
    renderAll();
    return;
  }
  state.selectedId = element.id;
  state.drag = {
    mode: handle ? "resize" : "move",
    handle,
    start: point,
    original: { x: Number(element.x || 0), y: Number(element.y || 0), w: Number(element.w || 1), h: Number(element.h || 1) },
    elementId: element.id,
    historyRecorded: false,
  };
  dom.selectionOverlay.setPointerCapture?.(event.pointerId);
  renderAll();
  showDragGhost(element);
  event.preventDefault();
}

function onPointerMove(event) {
  if (!state.drag) {
    return;
  }
  const element = elementById(state.drag.elementId);
  if (!element) {
    return;
  }
  if (!state.drag.historyRecorded) {
    recordHistory();
    state.drag.historyRecorded = true;
  }
  const point = eventToCanvas(event);
  const dx = Math.round(point.x - state.drag.start.x);
  const dy = Math.round(point.y - state.drag.start.y);
  const original = state.drag.original;
  if (state.drag.mode === "move") {
    element.x = original.x + dx;
    element.y = original.y + dy;
  } else {
    resizeElement(element, original, dx, dy, state.drag.handle);
  }
  Editor.normalizeElementForCanvas(element, state.layout.canvas || {});
  renderProperties();
  renderOverlay();
  updateDragGhost(element);
  schedulePreview(55);
  event.preventDefault();
}

function onPointerUp() {
  if (!state.drag) {
    return;
  }
  state.drag = null;
  markDirty();
  renderAll();
  schedulePreview(20);
}

function showDragGhost(element) {
  if (!dom.previewImage.src || !element) {
    hideDragGhost();
    return;
  }
  dom.dragGhost.hidden = false;
  dom.dragGhost.style.backgroundImage = `url("${dom.previewImage.src}")`;
  updateDragGhost(element);
}

function updateDragGhost(element) {
  if (dom.dragGhost.hidden || !element) {
    return;
  }
  const { width, height, sx, sy } = canvasScale();
  const style = DragGhost.computeDragGhostStyle(element, state.layout?.canvas, { width, height, sx, sy });
  Object.assign(dom.dragGhost.style, style);
}

function hideDragGhost() {
  if (!dom.dragGhost) {
    return;
  }
  dom.dragGhost.hidden = true;
  dom.dragGhost.style.backgroundImage = "";
}

function resizeElement(element, original, dx, dy, handle) {
  let x = original.x;
  let y = original.y;
  let w = original.w;
  let h = original.h;
  if (handle.includes("e")) {
    w = original.w + dx;
  }
  if (handle.includes("s")) {
    h = original.h + dy;
  }
  if (handle.includes("w")) {
    x = original.x + dx;
    w = original.w - dx;
  }
  if (handle.includes("n")) {
    y = original.y + dy;
    h = original.h - dy;
  }
  if (w < 8) {
    x = element.x;
    w = 8;
  }
  if (h < 8) {
    y = element.y;
    h = 8;
  }
  Object.assign(element, { x, y, w, h });
}

function onKeyDown(event) {
  const targetTag = String(event.target?.tagName || "").toLowerCase();
  const editingText = targetTag === "input" || targetTag === "select" || targetTag === "textarea";
  if (!editingText && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") {
    if (event.shiftKey) {
      redo();
    } else {
      undo();
    }
    event.preventDefault();
    return;
  }
  if (!editingText && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "y") {
    redo();
    event.preventDefault();
    return;
  }
  if (!editingText && state.selectedId && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "d") {
    duplicateSelected();
    event.preventDefault();
    return;
  }
  if (editingText) {
    return;
  }
  if (!state.selectedId) {
    return;
  }
  if (event.key === "Delete" || event.key === "Backspace") {
    deleteSelected();
    event.preventDefault();
    return;
  }
  const moves = {
    ArrowLeft: [-1, 0],
    ArrowRight: [1, 0],
    ArrowUp: [0, -1],
    ArrowDown: [0, 1],
  };
  if (!moves[event.key]) {
    return;
  }
  const element = selectedElement();
  if (!element) {
    return;
  }
  const step = event.shiftKey ? 10 : 1;
  element.x = Number(element.x || 0) + moves[event.key][0] * step;
  element.y = Number(element.y || 0) + moves[event.key][1] * step;
  Editor.normalizeElementForCanvas(element, state.layout.canvas || {});
  markDirty();
  renderAll();
  schedulePreview(50);
  event.preventDefault();
}

function deleteSelected() {
  if (!state.selectedId) {
    return;
  }
  recordHistory();
  state.layout.elements = (state.layout.elements || []).filter((element) => element.id !== state.selectedId);
  state.selectedId = "";
  markDirty();
  renderAll();
  schedulePreview(40);
}

function bumpZ(delta) {
  const element = selectedElement();
  if (!element) {
    return;
  }
  recordHistory();
  element.z = Number.parseInt(element.z || 0, 10) + delta;
  markDirty();
  renderLayers();
  renderOverlay();
  schedulePreview(40);
}

function eventToCanvas(event) {
  const canvas = state.layout.canvas || { width: 1920, height: 480 };
  const rect = dom.previewStage.getBoundingClientRect();
  return {
    x: Math.round(((event.clientX - rect.left) / rect.width) * Number(canvas.width || 1920)),
    y: Math.round(((event.clientY - rect.top) / rect.height) * Number(canvas.height || 480)),
  };
}

function canvasScale() {
  const canvas = state.layout?.canvas || { width: 1920, height: 480 };
  const stageRect = dom.previewStage.getBoundingClientRect();
  const canvasWidth = Number(canvas.width || 1920);
  const canvasHeight = Number(canvas.height || 480);
  return {
    sx: stageRect.width / canvasWidth,
    sy: stageRect.height / canvasHeight,
    width: stageRect.width,
    height: stageRect.height,
  };
}

function hitTest(x, y) {
  return [...(state.layout.elements || [])]
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

function selectedElement() {
  return elementById(state.selectedId);
}

function elementById(id) {
  if (!id) {
    return null;
  }
  return (state.layout.elements || []).find((element) => element.id === id) || null;
}

function propertyValue(element, key, type) {
  const value = element[key];
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (type === "color") {
    return validColor(value) ? value : "#ffffff";
  }
  return value ?? "";
}

function fieldApplies(key, element) {
  if (["value_style", "min_value", "max_value", "tick_interval"].includes(key)) {
    return element.type === "value";
  }
  if (["gear_style", "gears", "active_font_size"].includes(key)) {
    return element.type === "gear_indicator";
  }
  if (["event_binding", "side_binding"].includes(key)) {
    return element.type === "nav_icon";
  }
  return true;
}

function vehicleLabel(vehicleId) {
  const profile = state.vehicleProfiles?.[vehicleId];
  return profile?.label ? `${profile.label} (${vehicleId})` : vehicleId;
}

function markDirty() {
  state.dirty = true;
  Editor.syncCurrentScreen(state.layout, state.currentScreen);
  updateFilePath();
  renderTopControls();
}

function snapshotState() {
  return {
    layout: Editor.clone(state.layout),
    currentScreen: state.currentScreen,
    selectedId: state.selectedId,
  };
}

function recordHistory() {
  if (!state.layout || state.history.applying) {
    return;
  }
  pushUndoSnapshot(snapshotState());
  state.history.redo = [];
  renderTopControls();
}

function pushUndoSnapshot(snapshot) {
  if (!snapshot) {
    return;
  }
  state.history.undo.push(snapshot);
  if (state.history.undo.length > 50) {
    state.history.undo.shift();
  }
}

function restoreSnapshot(snapshot) {
  if (!snapshot) {
    return;
  }
  state.history.applying = true;
  state.layout = Editor.clone(snapshot.layout);
  state.currentScreen = snapshot.currentScreen;
  state.selectedId = snapshot.selectedId || "";
  state.dirty = true;
  state.history.applying = false;
  renderAll();
  schedulePreview(30);
}

function undo() {
  if (!state.history.undo.length) {
    return;
  }
  state.history.redo.push(snapshotState());
  restoreSnapshot(state.history.undo.pop());
}

function redo() {
  if (!state.history.redo.length) {
    return;
  }
  state.history.undo.push(snapshotState());
  restoreSnapshot(state.history.redo.pop());
}

function confirmDiscardChanges() {
  if (!state.dirty) {
    return true;
  }
  return window.confirm(`${t("unsaved")}. ${t("discardConfirm")}`);
}

function showValidationDrawer(messages) {
  state.validationMessages = messages || [];
  dom.validationMessages.replaceChildren();
  for (const message of state.validationMessages) {
    const item = document.createElement("div");
    item.className = "validation-message";
    item.textContent = message;
    dom.validationMessages.append(item);
  }
  dom.validationDrawer.hidden = false;
}

function hideValidationDrawer() {
  if (!dom.validationDrawer) {
    return;
  }
  state.validationMessages = [];
  dom.validationDrawer.hidden = true;
  dom.validationMessages?.replaceChildren();
}

function updateFilePath() {
  const marker = state.dirty ? ` · ${t("unsaved")}` : "";
  dom.filePath.textContent = `${state.path || "Untitled layout"}${marker}`;
  dom.filePath.classList.toggle("dirty", state.dirty);
}

function setStatus(message, kind = "") {
  dom.statusText.textContent = message;
  dom.statusText.parentElement.classList.toggle("ok", kind === "ok");
  dom.statusText.parentElement.classList.toggle("error", kind === "error");
}

function validColor(value) {
  return typeof value === "string" && /^#[0-9a-fA-F]{6}$/.test(value);
}

function applyLanguage() {
  document.documentElement.lang = state.appLanguage;
  for (const node of document.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.dataset.i18n);
  }
  for (const node of document.querySelectorAll("[data-i18n-placeholder]")) {
    node.placeholder = t(node.dataset.i18nPlaceholder);
  }
}

function t(key) {
  return I18N[state.appLanguage]?.[key] || I18N.en[key] || key;
}

function propertyLabel(key, fallback) {
  if (state.appLanguage === "ko") {
    return PROPERTY_LABELS_KO[key] || fallback;
  }
  return fallback;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
