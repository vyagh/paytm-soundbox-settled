// Builds ../d-scene.html from these sources and the anatomy skill's iso kit, inlined so the page stands alone.
// node board/proto/d-scene/build.mjs   (ANATOMY_KIT overrides where the kit is read from)
import { readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";

const KIT = process.env.ANATOMY_KIT || `${homedir()}/.claude/skills/anatomy/kit/iso-kit.mjs`;
const { ISO_CSS } = await import(KIT);
const here = f => readFileSync(new URL(f, import.meta.url), "utf8");
const inline = s => s.replace(/<\/script/gi, "<\\/script");
const kit = readFileSync(KIT, "utf8").replace(/^export /gm, "").replace(/^const ISO_CSS = `[\s\S]*?`;\n/m, "");

const page = here("template.html")
  .replace("/*STYLE*/", () => ISO_CSS.trim() + "\n" + here("style.css"))
  .replace("<!--BODY-->", () => here("body.html"))
  .replace("/*KIT*/", () => inline(kit))
  .replace("/*APP*/", () => inline(here("scene.js") + "\n" + here("app.js")));
writeFileSync(new URL("../d-scene.html", import.meta.url), page);
console.log(`d-scene.html ${page.length} bytes`);
