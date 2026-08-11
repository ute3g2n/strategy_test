const fs = require("fs");
const path = require("path");

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function inlineFormat(text) {
  let out = escapeHtml(text);
  out = out.replace(/`(\.\.\/\.\.\/\.\.\/\.\.\/doc\/ui_mock\/[^`]+#SCREEN-\d{2})`/g, '<a href="$1"><code>$1</code></a>');
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
  return out;
}

function slugify(text, used) {
  let slug = text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "-")
    .replace(/^-+|-+$/g, "");
  if (!slug) slug = "section";
  let candidate = slug;
  let i = 2;
  while (used.has(candidate)) {
    candidate = `${slug}-${i}`;
    i += 1;
  }
  used.add(candidate);
  return candidate;
}

function renderTable(lines) {
  if (lines.length < 2) return "";
  const rows = lines.map((line) =>
    line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => inlineFormat(cell.trim()))
  );
  const header = rows[0];
  const body = rows.slice(2);
  const thead = `<thead><tr>${header.map((c) => `<th>${c}</th>`).join("")}</tr></thead>`;
  const tbody = `<tbody>${body
    .map((row) => `<tr>${row.map((c) => `<td>${c}</td>`).join("")}</tr>`)
    .join("")}</tbody>`;
  return `<table>${thead}${tbody}</table>`;
}

function renderMarkdown(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const usedIds = new Set();
  const toc = [];
  const out = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      i += 1;
      continue;
    }

    if (trimmed.startsWith("```")) {
      const lang = trimmed.slice(3).trim();
      const code = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        code.push(lines[i]);
        i += 1;
      }
      i += 1;
      if (lang === "mermaid") {
        out.push(`<div class="mermaid">${escapeHtml(code.join("\n"))}</div>`);
        continue;
      }
      out.push(
        `<pre><code${lang ? ` class="language-${escapeHtml(lang)}"` : ""}>${escapeHtml(
          code.join("\n")
        )}</code></pre>`
      );
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      const text = heading[2].trim();
      const id = slugify(text, usedIds);
      if (level <= 3) {
        toc.push({ level, text, id });
      }
      out.push(`<h${level} id="${id}">${inlineFormat(text)}</h${level}>`);
      i += 1;
      continue;
    }

    if (/^-{3,}$/.test(trimmed)) {
      out.push("<hr>");
      i += 1;
      continue;
    }

    if (trimmed.startsWith(">")) {
      const parts = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        parts.push(lines[i].trim().replace(/^>\s?/, ""));
        i += 1;
      }
      out.push(`<blockquote><p>${inlineFormat(parts.join(" "))}</p></blockquote>`);
      continue;
    }

    if (trimmed.includes("|") && i + 1 < lines.length && /^\s*\|?[\s:-]+\|[\s|:-]*$/.test(lines[i + 1])) {
      const tableLines = [line, lines[i + 1]];
      i += 2;
      while (i < lines.length && lines[i].trim().includes("|")) {
        tableLines.push(lines[i]);
        i += 1;
      }
      out.push(renderTable(tableLines));
      continue;
    }

    if (/^- /.test(trimmed)) {
      const items = [];
      while (i < lines.length && /^- /.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^- /, ""));
        i += 1;
      }
      out.push(`<ul>${items.map((item) => `<li>${inlineFormat(item)}</li>`).join("")}</ul>`);
      continue;
    }

    if (/^\d+\.\s/.test(trimmed)) {
      const items = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s/, ""));
        i += 1;
      }
      out.push(`<ol>${items.map((item) => `<li>${inlineFormat(item)}</li>`).join("")}</ol>`);
      continue;
    }

    const para = [];
    while (i < lines.length) {
      const current = lines[i].trim();
      if (
        !current ||
        current.startsWith("```") ||
        /^(#{1,6})\s+/.test(current) ||
        /^-{3,}$/.test(current) ||
        current.startsWith(">") ||
        /^- /.test(current) ||
        /^\d+\.\s/.test(current) ||
        (current.includes("|") && i + 1 < lines.length && /^\s*\|?[\s:-]+\|[\s|:-]*$/.test(lines[i + 1]))
      ) {
        break;
      }
      para.push(current);
      i += 1;
    }
    out.push(`<p>${inlineFormat(para.join(" "))}</p>`);
  }

  return { html: out.join("\n"), toc };
}

function renderToc(toc) {
  if (!toc.length) return "";
  return `<nav class="toc" aria-label="目次"><h2>目次</h2><ul>${toc
    .map((item) => `<li class="lvl-${item.level}"><a href="#${item.id}">${escapeHtml(item.text)}</a></li>`)
    .join("")}</ul></nav>`;
}

function main() {
  const inputPath = path.resolve(process.argv[2]);
  const outputPath = path.resolve(process.argv[3]);
  const markdown = fs.readFileSync(inputPath, "utf8");
  const firstHeading = markdown.match(/^#\s+(.+)$/m);
  const title = firstHeading ? firstHeading[1].trim() : path.basename(inputPath, path.extname(inputPath));
  const rendered = renderMarkdown(markdown);
  const repoRelative = (value) => path.relative(process.cwd(), value).split(path.sep).join("/");
  const htmlRelative = (value) => path.relative(path.dirname(outputPath), value).split(path.sep).join("/");
  const inputDisplay = repoRelative(inputPath);
  const outputDisplay = repoRelative(outputPath);
  const mermaidJs = htmlRelative(path.resolve(__dirname, "../doc/assets/mermaid.min.js"));
  const mermaidInit = htmlRelative(path.resolve(__dirname, "../doc/assets/mermaid-init.js"));

  const html = `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)}</title>
  <style>
    :root { color-scheme: light; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.75; margin: 40px auto; max-width: 1200px; color: #1f2937; background: #f8fafc; }
    main { background: #fff; border: 1px solid #d9e2ec; padding: 28px; }
    h1, h2, h3, h4 { color: #111827; letter-spacing: 0; }
    h1 { border-bottom: 3px solid #111827; padding-bottom: 8px; }
    h2 { border-bottom: 1px solid #d1d5db; padding-bottom: 4px; margin-top: 32px; }
    table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }
    th, td { border: 1px solid #d1d5db; padding: 8px 10px; vertical-align: top; }
    th { background: #f3f4f6; }
    code { background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }
    pre { background: #111827; color: #f9fafb; padding: 16px; overflow-x: auto; }
    blockquote { border-left: 4px solid #2563eb; padding: 8px 14px; background: #eff6ff; margin: 16px 0; }
    a { color: #1d4ed8; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .meta { border-left: 4px solid #2563eb; padding: 10px 14px; background: #eff6ff; margin: 16px 0; }
    .mermaid { background: #fff; border: 1px solid #d1d5db; padding: 16px; margin: 20px 0; overflow-x: auto; }
    .toc ul { list-style: none; padding-left: 0; }
    .toc li { margin: 6px 0; }
    .toc .lvl-2 { padding-left: 12px; }
    .toc .lvl-3 { padding-left: 24px; }
    @media (max-width: 700px) { body { margin: 0; } main { border-left: 0; border-right: 0; padding: 16px; } table { display: block; overflow-x: auto; } .mermaid { min-width: 680px; } }
    @media print { body { margin: 0; background: #fff; } main { max-width: none; border: 0; } h1, h2, h3, h4, table, figure { break-inside: avoid; } a { color: #000; text-decoration: none; } .mermaid { min-width: 0; } }
  </style>
</head>
<body>
<main>
  <section class="meta">
    <p><strong>文書種別:</strong> 要件定義書 HTML化成果物<br>
    <strong>元ファイル:</strong> <code>${escapeHtml(inputDisplay)}</code><br>
    <strong>保存先:</strong> <code>${escapeHtml(outputDisplay)}</code></p>
  </section>
  ${renderToc(rendered.toc)}
  ${rendered.html}
</main>
<script src="${escapeHtml(mermaidJs)}"></script>
<script src="${escapeHtml(mermaidInit)}"></script>
</body>
</html>
`;

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, html, "utf8");
}

main();
