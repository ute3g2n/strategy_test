import fs from "node:fs";
import { JSDOM } from "file:///C:/Users/ute3g/AppData/Local/Temp/rqu-mermaid-runtime/node_modules/jsdom/lib/api.js";

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  pretendToBeVisual: true,
});
const windowObject = dom.window;
for (const name of [
  "window",
  "document",
  "navigator",
  "Option",
  "Element",
  "HTMLElement",
  "SVGElement",
  "XMLSerializer",
  "DOMParser",
  "CSSStyleSheet",
  "Node",
  "MutationObserver",
  "getComputedStyle",
]) {
  Object.defineProperty(globalThis, name, {
    configurable: true,
    value: windowObject[name],
  });
}
if (!windowObject.SVGElement.prototype.getBBox) {
  windowObject.SVGElement.prototype.getBBox = () => ({
    height: 20,
    width: 100,
    x: 0,
    y: 0,
  });
}

const mermaidModule = await import("mermaid");
mermaidModule.default.initialize({
  securityLevel: "loose",
  startOnLoad: false,
});

const html = fs.readFileSync(
  "plan/requirements_update/evidence/mermaid/RQU-04_mermaid_probe.html",
  "utf8",
);
const blocks = html
  .split('<div class="mermaid">')
  .slice(1)
  .map((part) => part.split("</div>")[0].trim());

console.log(`PROBE_BLOCKS=${blocks.length}`);
for (let index = 0; index < blocks.length; index += 1) {
  try {
    const result = await mermaidModule.default.parse(blocks[index]);
    console.log(`PROBE_${index + 1}=PASS diagramType=${result.diagramType}`);
    const rendered = await mermaidModule.default.render(
      `rqu04_probe_${index + 1}`,
      blocks[index],
    );
    const svgPass = rendered.svg.includes("<svg");
    console.log(`RENDER_${index + 1}=${svgPass ? "PASS" : "FAIL"}`);
    if (!svgPass) {
      process.exitCode = 1;
    }
  } catch (error) {
    console.log(`PROBE_${index + 1}=FAIL ${error?.message ?? error}`);
    process.exitCode = 1;
  }
}
