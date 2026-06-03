const fs = require("node:fs/promises");
const path = require("node:path");
const sharp = require("sharp");

const ROOT = path.resolve(__dirname, "..", "..");
const MATERIAL_FILLED = path.join(
  __dirname,
  "..",
  "node_modules",
  "@material-design-icons",
  "svg",
  "filled"
);
const OUTPUT_DIR = path.join(ROOT, "pi-hud", "assets", "nav-icons");

// Map internal names to Material Design Icon filenames
const ICONS = {
  turn_left: "turn_left.svg",
  turn_right: "turn_right.svg",
  u_turn_left: "u_turn_left.svg",
  u_turn_right: "u_turn_right.svg",
  straight: "arrow_upward.svg",
  roundabout_left: "roundabout_left.svg",
  roundabout_right: "roundabout_right.svg",
  flag: "map.svg",
};

async function main() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  for (const [name, source] of Object.entries(ICONS)) {
    const sourcePath = path.join(MATERIAL_FILLED, source);
    try {
      await sharp(sourcePath)
        .resize(128, 128, { fit: "contain" })
        .png()
        .toFile(path.join(OUTPUT_DIR, `${name}.png`));
      console.log(`Generated ${name}.png`);
    } catch (err) {
      console.error(`Failed to generate ${name}: ${err.message}`);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
