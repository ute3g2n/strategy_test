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
        height: calc(100vh - 92px) !important;
        min-height: calc(100vh - 92px) !important;
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

  function getBaseSize(svg) {
    const viewBox = svg.viewBox && svg.viewBox.baseVal;
    const width = viewBox && viewBox.width ? viewBox.width : (svg.getBBox().width || 1);
    const height = viewBox && viewBox.height ? viewBox.height : (svg.getBBox().height || 1);
    return { width, height };
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

      function applyScale() {
        const svg = viewport.querySelector("svg");
        if (!svg) {
          return;
        }

        const baseWidth = Number(svg.dataset.baseWidth || 0);
        const baseHeight = Number(svg.dataset.baseHeight || 0);
        if (!baseWidth || !baseHeight) {
          return;
        }

        const scaledWidth = Math.max(baseWidth * scale, 1);
        const scaledHeight = Math.max(baseHeight * scale, 1);

        svg.style.width = `${scaledWidth}px`;
        svg.style.height = `${scaledHeight}px`;

        if (!shell.classList.contains("diagram-expanded")) {
          const viewportHeight = Math.max(scaledHeight + 32, 180);
          viewport.style.height = `${viewportHeight}px`;
          viewport.style.minHeight = `${viewportHeight}px`;
        }

        label.textContent = mode === "fit"
          ? `幅合わせ ${Math.round(scale * 100)}%`
          : `${Math.round(scale * 100)}%`;
      }

      function fitToWidth() {
        const svg = viewport.querySelector("svg");
        if (!svg) {
          return;
        }

        const baseWidth = Number(svg.dataset.baseWidth || 0);
        if (!baseWidth) {
          return;
        }

        const available = Math.max(viewport.clientWidth - 32, 240);
        scale = Math.max(0.4, Math.min(available / baseWidth, 3));
        mode = "fit";
        applyScale();
      }

      toolbar.appendChild(createButton("拡大", () => {
        scale = Math.min(scale + 0.2, 3);
        mode = "manual";
        applyScale();
      }));

      toolbar.appendChild(createButton("縮小", () => {
        scale = Math.max(scale - 0.2, 0.4);
        mode = "manual";
        applyScale();
      }));

      toolbar.appendChild(createButton("等倍", () => {
        scale = 1;
        mode = "manual";
        applyScale();
      }));

      toolbar.appendChild(createButton("幅合わせ", () => {
        fitToWidth();
      }));

      toolbar.appendChild(createButton("最大化", (event) => {
        shell.classList.toggle("diagram-expanded");
        event.currentTarget.textContent = shell.classList.contains("diagram-expanded")
          ? "閉じる"
          : "最大化";

        requestAnimationFrame(() => {
          if (mode === "fit") {
            fitToWidth();
          } else {
            applyScale();
          }
        });
      }));

      toolbar.appendChild(label);

      node.parentNode.insertBefore(shell, node);
      viewport.appendChild(node);
      shell.appendChild(toolbar);
      shell.appendChild(viewport);

      node._applyDiagramScale = applyScale;
      node._fitDiagramToWidth = fitToWidth;

      window.addEventListener("resize", () => {
        if (mode === "fit") {
          fitToWidth();
        } else {
          applyScale();
        }
      });
    });
  }

  async function render() {
    if (typeof mermaid === "undefined") {
      return false;
    }

    injectStyles();
    wrapDiagrams();

    const nodes = [...document.querySelectorAll(".mermaid")]
      .filter((node) => !node.querySelector("svg"));

    if (nodes.length === 0) {
      return true;
    }

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

    if (typeof mermaid.run === "function") {
      await mermaid.run({ nodes });
    } else if (typeof mermaid.init === "function") {
      await mermaid.init(undefined, nodes);
    } else {
      throw new Error("Mermaid rendering API is unavailable");
    }

    document.querySelectorAll(".mermaid").forEach((node) => {
      const svg = node.querySelector("svg");
      if (!svg) {
        return;
      }

      const base = getBaseSize(svg);
      svg.dataset.baseWidth = String(base.width);
      svg.dataset.baseHeight = String(base.height);

      if (typeof node._fitDiagramToWidth === "function") {
        node._fitDiagramToWidth();
      } else if (typeof node._applyDiagramScale === "function") {
        node._applyDiagramScale();
      }
    });

    return nodes.every((node) => Boolean(node.querySelector("svg")));
  }

  function scheduleRender() {
    let attempts = 0;
    let rendering = false;

    const attempt = () => {
      if (rendering) {
        return;
      }

      const hasUnrendered = [...document.querySelectorAll(".mermaid")]
        .some((node) => !node.querySelector("svg"));

      if (!hasUnrendered) {
        return;
      }

      rendering = true;
      render().then((complete) => {
        if (!complete && attempts < 20) {
          attempts += 1;
          window.setTimeout(attempt, 250);
        }
      }).catch((error) => {
        console.error("Mermaid diagram rendering failed", error);
        if (attempts < 20) {
          attempts += 1;
          window.setTimeout(attempt, 250);
        }
      }).finally(() => {
        rendering = false;
      });
    };

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", attempt, { once: true });
    } else {
      attempt();
    }

    window.addEventListener("load", attempt, { once: true });
  }

  scheduleRender();
})();
