(() => {
  if (typeof mermaid === "undefined") {
    return;
  }

  function injectStyles() {
    if (document.getElementById("mermaid-zoom-styles")) {
      return;
    }
    const style = document.createElement("style");
    style.id = "mermaid-zoom-styles";
    style.textContent = `
      .diagram-shell {
        border: 1px solid #cbd5e1;
        background: #fff;
        margin: 16px 0;
      }
      .diagram-toolbar {
        display: flex;
        gap: 8px;
        align-items: center;
        padding: 10px 12px;
        border-bottom: 1px solid #e5e7eb;
        background: #f8fafc;
        position: sticky;
        top: 0;
        z-index: 2;
      }
      .diagram-toolbar button {
        border: 1px solid #cbd5e1;
        background: #fff;
        color: #0f172a;
        padding: 6px 10px;
        border-radius: 6px;
        cursor: pointer;
        font: inherit;
      }
      .diagram-toolbar button:hover {
        background: #eff6ff;
      }
      .diagram-zoom-label {
        color: #475569;
        font-size: 13px;
        margin-left: 4px;
      }
      .diagram-viewport {
        overflow: auto;
        padding: 16px;
        background: #fff;
        min-height: 180px;
      }
      .diagram-viewport .mermaid {
        min-width: 100%;
        width: 100%;
      }
      .diagram-viewport svg {
        display: block;
        transform-origin: top left;
        transition: transform 0.15s ease;
        max-width: none !important;
        height: auto;
      }
      .diagram-shell.diagram-expanded {
        position: fixed;
        inset: 16px;
        z-index: 9999;
        box-shadow: 0 20px 60px rgba(15, 23, 42, 0.28);
      }
      .diagram-shell.diagram-expanded .diagram-viewport {
        height: calc(100vh - 92px);
      }
    `;
    document.head.appendChild(style);
  }

  function createButton(label, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", onClick);
    return button;
  }

  function wrapDiagrams() {
    document.querySelectorAll(".mermaid").forEach((node) => {
      if (node.closest(".diagram-shell")) {
        return;
      }
      const shell = document.createElement("div");
      shell.className = "diagram-shell";
      const toolbar = document.createElement("div");
      toolbar.className = "diagram-toolbar";
      const viewport = document.createElement("div");
      viewport.className = "diagram-viewport";
      const label = document.createElement("span");
      label.className = "diagram-zoom-label";
      label.textContent = "幅合わせ";

      let scale = 1;
      let mode = "fit";
      const updateScale = () => {
        const svg = viewport.querySelector("svg");
        if (svg) {
          svg.style.transform = `scale(${scale})`;
          const width = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width
            ? svg.viewBox.baseVal.width
            : svg.getBBox().width || svg.getBoundingClientRect().width || 1;
          const height = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.height
            ? svg.viewBox.baseVal.height
            : svg.getBBox().height || svg.getBoundingClientRect().height || 1;
          svg.style.width = `${width}px`;
          svg.style.height = `${height}px`;
          const scaledHeight = Math.max(height * scale + 32, 180);
          viewport.style.minHeight = `${scaledHeight}px`;
        }
        label.textContent = mode === "fit" ? `幅合わせ ${Math.round(scale * 100)}%` : `${Math.round(scale * 100)}%`;
      };

      const fitToWidth = () => {
        const svg = viewport.querySelector("svg");
        if (!svg) {
          return;
        }
        const width = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width
          ? svg.viewBox.baseVal.width
          : svg.getBBox().width || svg.getBoundingClientRect().width || 1;
        const available = Math.max(viewport.clientWidth - 32, 240);
        scale = Math.max(0.4, Math.min(available / width, 3));
        mode = "fit";
        updateScale();
      };

      toolbar.appendChild(createButton("拡大", () => {
        scale = Math.min(scale + 0.2, 3);
        mode = "manual";
        updateScale();
      }));
      toolbar.appendChild(createButton("縮小", () => {
        scale = Math.max(scale - 0.2, 0.4);
        mode = "manual";
        updateScale();
      }));
      toolbar.appendChild(createButton("等倍", () => {
        scale = 1;
        mode = "manual";
        updateScale();
      }));
      toolbar.appendChild(createButton("幅合わせ", () => {
        fitToWidth();
      }));
      toolbar.appendChild(createButton("最大化", (event) => {
        shell.classList.toggle("diagram-expanded");
        event.currentTarget.textContent = shell.classList.contains("diagram-expanded") ? "閉じる" : "最大化";
        requestAnimationFrame(() => {
          if (mode === "fit") {
            fitToWidth();
          } else {
            updateScale();
          }
        });
      }));
      toolbar.appendChild(label);

      node.parentNode.insertBefore(shell, node);
      viewport.appendChild(node);
      shell.appendChild(toolbar);
      shell.appendChild(viewport);

      node.dataset.zoomReady = "true";
      node._updateDiagramScale = updateScale;
      node._fitDiagramToWidth = fitToWidth;

      window.addEventListener("resize", () => {
        if (mode === "fit") {
          fitToWidth();
        }
      });
    });
  }

  async function render() {
    injectStyles();
    wrapDiagrams();
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      theme: "default",
      flowchart: {
        htmlLabels: true,
        curve: "basis",
        useMaxWidth: false
      }
    });
    await mermaid.run({ querySelector: ".mermaid" });
    document.querySelectorAll(".mermaid").forEach((node) => {
      if (typeof node._fitDiagramToWidth === "function") {
        node._fitDiagramToWidth();
      } else if (typeof node._updateDiagramScale === "function") {
        node._updateDiagramScale();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      render();
    });
  } else {
    render();
  }
})();
