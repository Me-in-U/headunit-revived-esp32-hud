const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const rendererDir = path.join(__dirname, "..", "src", "renderer");
const indexPath = path.join(rendererDir, "index.html");

test("connection panel keeps OBD and CAN setup only", () => {
  const content = fs.readFileSync(indexPath, "utf8");
  const connectionPanel = sectionContent(content, "connectionPanel", "canAnalysisPanel");

  assert.match(connectionPanel, /class="connection-layout"/);
  assert.match(connectionPanel, /OBD Bluetooth/);
  assert.match(connectionPanel, /CANable USB/);
  assert.doesNotMatch(connectionPanel, /id="liveSampleStatus"/);
  assert.doesNotMatch(connectionPanel, /id="copyLiveSampleBtn"/);
});

test("CAN analysis panel owns the live sample and live log rail", () => {
  const content = fs.readFileSync(indexPath, "utf8");
  const canPanel = sectionContent(content, "canAnalysisPanel", "obdAnalysisPanel");

  assert.match(canPanel, /class="can-analysis-layout"/);
  assert.match(canPanel, /class="live-log-panel"/);
  assert.match(canPanel, /id="liveCanStatus"/);
  assert.match(canPanel, /id="liveObdStatus"/);
  assert.match(canPanel, /id="liveLogList"/);
  assert.match(canPanel, /id="liveSampleStatus"/);
  assert.match(canPanel, /id="copyLiveSampleBtn"/);
});

function sectionContent(content, startId, nextId) {
  const start = content.indexOf(`id="${startId}"`);
  const end = content.indexOf(`id="${nextId}"`);
  assert.notEqual(start, -1, `${startId} should exist`);
  assert.notEqual(end, -1, `${nextId} should exist`);
  assert.equal(start < end, true, `${startId} should appear before ${nextId}`);
  return content.slice(start, end);
}
