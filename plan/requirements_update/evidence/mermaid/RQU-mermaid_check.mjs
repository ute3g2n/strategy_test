import fs from "node:fs";
import { JSDOM } from "file:///C:/Users/ute3g/AppData/Local/Temp/rqu-mermaid-runtime/node_modules/jsdom/lib/api.js";

const inputPath = process.argv[2];
if (!inputPath) {
  throw new Error("Usage: node RQU-mermaid_check.mjs <markdown-or-html>");
}

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

const source = fs.readFileSync(inputPath, "utf8");
const blocks = inputPath.endsWith(".html")
  ? source
      .split('<div class="mermaid">')
      .slice(1)
      .map((part) => part.split("</div>")[0].trim())
  : source
      .split("```mermaid")
      .slice(1)
      .map((part) => part.split("```")[0].trim());

console.log(`INPUT=${inputPath}`);
console.log(`BLOCKS=${blocks.length}`);
for (let index = 0; index < blocks.length; index += 1) {
  try {
    const parsed = await mermaidModule.default.parse(blocks[index]);
    const rendered = await mermaidModule.default.render(
      `rqu_check_${Date.now()}_${index}`,
      blocks[index],
    );
    const pass = rendered.svg.includes("<svg");
    console.log(
      `BLOCK_${index + 1}=${pass ? "PASS" : "FAIL"} diagramType=${parsed.diagramType}`,
    );
    if (!pass) {
      process.exitCode = 1;
    }
  } catch (error) {
    console.log(`BLOCK_${index + 1}=FAIL ${error?.message ?? error}`);
    process.exitCode = 1;
  }
}
