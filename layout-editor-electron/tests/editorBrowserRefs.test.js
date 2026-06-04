const assert = require("node:assert/strict");
const test = require("node:test");

const BrowserRefs = require("../src/renderer/editorBrowserRefs.js");

test("createBrowserRefs preserves window receiver for browser timer APIs", () => {
  const calls = [];
  const documentRef = {};
  const dom = {};
  const localStorageRef = {};
  const navigatorRef = {};
  const windowRef = {
    clearTimeout(timer) {
      assert.equal(this, windowRef);
      calls.push(["clearTimeout", timer]);
    },
    requestAnimationFrame(callback) {
      assert.equal(this, windowRef);
      calls.push(["requestAnimationFrame", callback]);
      callback();
    },
    setTimeout(callback, delay) {
      assert.equal(this, windowRef);
      calls.push(["setTimeout", delay]);
      callback();
      return "timer-id";
    },
  };
  let frameCallbackRan = false;
  let timeoutCallbackRan = false;

  const refs = BrowserRefs.createBrowserRefs({
    documentRef,
    dom,
    localStorageRef,
    navigatorRef,
    windowRef,
  });

  refs.requestAnimationFrameRef(() => {
    frameCallbackRan = true;
  });
  const timerId = refs.setTimeoutRef(() => {
    timeoutCallbackRan = true;
  }, 30);
  refs.clearTimeoutRef(timerId);

  assert.equal(refs.documentRef, documentRef);
  assert.equal(refs.dom, dom);
  assert.equal(refs.localStorageRef, localStorageRef);
  assert.equal(refs.navigatorRef, navigatorRef);
  assert.equal(refs.windowRef, windowRef);
  assert.equal(frameCallbackRan, true);
  assert.equal(timeoutCallbackRan, true);
  assert.equal(typeof calls[0][1], "function");
  assert.deepEqual(calls.map(([name, value]) => [name, name === "requestAnimationFrame" ? "callback" : value]), [
    ["requestAnimationFrame", "callback"],
    ["setTimeout", 30],
    ["clearTimeout", "timer-id"],
  ]);
});
