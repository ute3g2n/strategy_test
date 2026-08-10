import fs from "node:fs";

const [markdownPath, htmlPath] = process.argv.slice(2);
if (!markdownPath || !htmlPath) {
  throw new Error("Usage: node RQU-requirement_id_sync_check.mjs <markdown> <html>");
}

const pattern = /REQ-(?:CTX|DATA|STR|BT|EXE|RISK|OPS|QA|GATE)-\d{3}/g;
const readIds = (path) =>
  [...new Set(fs.readFileSync(path, "utf8").match(pattern) ?? [])].sort();
const markdownIds = readIds(markdownPath);
const htmlIds = readIds(htmlPath);
const markdownOnly = markdownIds.filter((id) => !htmlIds.includes(id));
const htmlOnly = htmlIds.filter((id) => !markdownIds.includes(id));

console.log(`MARKDOWN_IDS=${markdownIds.length}`);
console.log(`HTML_IDS=${htmlIds.length}`);
console.log(`MARKDOWN_ONLY=${markdownOnly.join(",") || "NONE"}`);
console.log(`HTML_ONLY=${htmlOnly.join(",") || "NONE"}`);
console.log(`SYNC=${markdownOnly.length === 0 && htmlOnly.length === 0 ? "PASS" : "FAIL"}`);
if (markdownOnly.length || htmlOnly.length) {
  process.exitCode = 1;
}
