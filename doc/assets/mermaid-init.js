(() => {
  if (typeof mermaid === "undefined") {
    return;
  }

  mermaid.initialize({
    startOnLoad: true,
    securityLevel: "loose",
    theme: "default",
    flowchart: {
      htmlLabels: true,
      curve: "basis",
      useMaxWidth: true
    }
  });
})();
