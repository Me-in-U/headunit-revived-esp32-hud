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
  assert.match(connectionPanel, /OBD 연결/);
  assert.match(connectionPanel, /id="obdSerialPort"/);
  assert.match(connectionPanel, /id="obdSerialPortList"/);
  assert.match(connectionPanel, /id="scanObdComPortsBtn"/);
  assert.match(connectionPanel, /id="startObdLiveBtn"/);
  assert.match(connectionPanel, /id="stopObdLiveBtn"/);
  assert.match(connectionPanel, /Android-vlink/);
  assert.match(connectionPanel, /CANable 연결/);
  assert.match(connectionPanel, /id="comPortList"/);
  assert.match(connectionPanel, /id="startCanLiveBtn"/);
  assert.match(connectionPanel, /id="stopCanLiveBtn"/);
  assert.doesNotMatch(connectionPanel, /id="startVehicleLiveBtn"/);
  assert.doesNotMatch(connectionPanel, /id="stopVehicleLiveBtn"/);
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

test("OBD analysis panel separates decoded values from raw responses", () => {
  const content = fs.readFileSync(indexPath, "utf8");
  const start = content.indexOf('id="obdAnalysisPanel"');
  const end = content.indexOf('class="sidebar inspector-panel"');
  assert.notEqual(start, -1, "obdAnalysisPanel should exist");
  assert.notEqual(end, -1, "inspector panel should exist");
  const obdPanel = content.slice(start, end);

  assert.match(obdPanel, /디코딩 값/);
  assert.match(obdPanel, /class="obd-section obd-values-section"/);
  assert.match(obdPanel, /id="obdAnalysisStatus"/);
  assert.match(obdPanel, /id="obdValueList"/);
  assert.match(obdPanel, /Raw 응답/);
  assert.match(obdPanel, /class="obd-section obd-raw-section"/);
  assert.match(obdPanel, /id="obdRecordList"/);
});

function sectionContent(content, startId, nextId) {
  const start = content.indexOf(`id="${startId}"`);
  const end = content.indexOf(`id="${nextId}"`);
  assert.notEqual(start, -1, `${startId} should exist`);
  assert.notEqual(end, -1, `${nextId} should exist`);
  assert.equal(start < end, true, `${startId} should appear before ${nextId}`);
  return content.slice(start, end);
}
