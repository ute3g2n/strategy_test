import fs from "node:fs";
import path from "node:path";
import { JSDOM } from "file:///C:/Users/ute3g/AppData/Local/Temp/rqu-mermaid-runtime/node_modules/jsdom/lib/api.js";

const inputPath = process.argv[2];
if (!inputPath) {
  throw new Error("Usage: node RQU-html_candidate_check.mjs <html>");
}

const source = fs.readFileSync(inputPath, "utf8");
const dom = new JSDOM(source, { url: "file:///" + inputPath.replaceAll("\\", "/") });
const document = dom.window.document;
const failures = [];

const check = (name, condition, detail = "") => {
  const status = condition ? "PASS" : "FAIL";
  console.log(`${name}=${status}${detail ? ` ${detail}` : ""}`);
  if (!condition) failures.push(name);
};

check("UTF8", !source.includes("\uFFFD"));
check("HTML_PARSE", Boolean(document.querySelector("html")) && Boolean(document.querySelector("main")));
check("TOC", Boolean(document.querySelector('nav[aria-label="目次"]')) && document.querySelectorAll("nav a[href^='#']").length >= 8);

const ids = new Set([...document.querySelectorAll("[id]")].map((element) => element.id));
const anchorLinks = [...document.querySelectorAll('a[href^="#"]')];
const missingAnchors = anchorLinks
  .map((link) => link.getAttribute("href").slice(1))
  .filter((id) => !ids.has(id));
check("ANCHOR_LINKS", missingAnchors.length === 0, `count=${anchorLinks.length}`);
if (missingAnchors.length > 0) console.log(`MISSING_ANCHORS=${missingAnchors.join(",")}`);

const externalLinks = [];
const brokenLocalLinks = [];
for (const link of [...document.querySelectorAll("a[href]")]) {
  const href = link.getAttribute("href");
  if (!href || href.startsWith("#") || /^[a-z][a-z0-9+.-]*:/i.test(href)) continue;
  const target = href.split("#", 1)[0];
  if (target.startsWith("http://") || target.startsWith("https://")) {
    externalLinks.push(href);
    continue;
  }
  const resolved = path.resolve(path.dirname(inputPath), target);
  if (!fs.existsSync(resolved)) brokenLocalLinks.push(`${href} -> ${resolved}`);
}
check("LOCAL_LINKS", brokenLocalLinks.length === 0, `external=${externalLinks.length}`);
for (const item of brokenLocalLinks) console.log(`BROKEN_LOCAL_LINK=${item}`);

const mermaidBlocks = [...document.querySelectorAll(".mermaid")];
const emptyMermaid = mermaidBlocks.filter((block) => block.textContent.trim().length === 0);
check("MERMAID_BLOCKS", mermaidBlocks.length > 0 && emptyMermaid.length === 0, `count=${mermaidBlocks.length}`);

const styleText = [...document.querySelectorAll("style")].map((style) => style.textContent).join("\n");
check("RESPONSIVE_CSS", /@media\s*\(max-width\s*:\s*700px\)/.test(styleText) && /overflow-x\s*:\s*auto/.test(styleText));
check("PRINT_CSS", /@media\s+print/.test(styleText) && /break-inside\s*:\s*avoid/.test(styleText));
check("LOCAL_MERMAID_ASSETS", [...document.querySelectorAll('script[src]')].every((script) => {
  const src = script.getAttribute("src");
  return src.startsWith("..") && fs.existsSync(path.resolve(path.dirname(inputPath), src));
}));

if (failures.length > 0) {
  console.log(`SUMMARY=FAIL ${failures.join(",")}`);
  process.exitCode = 1;
} else {
  console.log("SUMMARY=PASS");
}
