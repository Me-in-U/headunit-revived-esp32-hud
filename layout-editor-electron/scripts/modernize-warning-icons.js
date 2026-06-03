const fs = require("node:fs/promises");
const path = require("node:path");
const sharp = require("sharp");

const ROOT = path.resolve(__dirname, "..", "..");
const SVG_DIR = path.join(ROOT, "pi-hud", "assets", "warning-icons", "svg");
const OUTPUT_DIR = path.join(ROOT, "pi-hud", "assets", "warning-icons");

const RED = "#EE2024";
const AMBER = "#FFAE00";
const GREEN = "#24D36B";
const BLUE = "#40A7FF";

const ICONS = {
  abs: AMBER,
  airbag: RED,
  battery: RED,
  brake: RED,
  check_engine: AMBER,
  coolant_temp: RED,
  door_open: RED,
  eps: RED,
  oil_pressure: RED,
  seatbelt: RED,
  low_fuel: AMBER,
  tire_pressure: AMBER,
  high_beam: BLUE,
  low_beam: GREEN,
  parking_lights: GREEN,
  fog_light: GREEN,
  washer_fluid: AMBER,
  cruise_control: GREEN,
  traction_control: AMBER,
  glow_plug: AMBER,
};

function doorOpenSvg(color) {
  return `
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <g fill="none" stroke="${color}" stroke-linecap="round" stroke-linejoin="round">
    <rect x="42" y="14" width="44" height="100" rx="10" stroke-width="7"/>
    <path d="M42 55 18 82M42 70 18 98M86 55 110 82M86 70 110 98" stroke-width="8"/>
  </g>
  <g fill="${color}">
    <path d="M50 34H78L83 50H45Z"/>
    <path d="M46 78H82L77 94H51Z"/>
    <circle cx="42" cy="63" r="4"/>
    <circle cx="86" cy="63" r="4"/>
  </g>
</svg>`;
}

async function main() {
  const requested = new Set(process.argv.slice(2));
  for (const [name, color] of Object.entries(ICONS)) {
    if (requested.size > 0 && !requested.has(name)) {
      continue;
    }
    const svgPath = path.join(SVG_DIR, `${name}.svg`);
    try {
      let svgContent = name === "door_open" ? doorOpenSvg(color) : await fs.readFile(svgPath, "utf8");

      // Inject or replace fill color
      if (name === "door_open") {
        // Keep the HUD-specific top-view open-door silhouette instead of the generic side-view SVG.
      } else if (svgContent.includes("fill=\"currentColor\"")) {
        svgContent = svgContent.replace(/fill="currentColor"/g, `fill="${color}"`);
      } else if (!svgContent.includes("fill=")) {
        svgContent = svgContent.replace("<svg", `<svg fill="${color}"`);
      } else {
        svgContent = svgContent.replace(/fill="[^"]*"/g, `fill="${color}"`);
      }

      await sharp(Buffer.from(svgContent))
        .resize(128, 128, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
        .png()
        .toFile(path.join(OUTPUT_DIR, `${name}.png`));

      console.log(`Generated ${name}.png`);
    } catch (error) {
      console.error(`Failed to generate ${name}:`, error.message);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
