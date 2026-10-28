# Rebuild the offline study

Reading requires only a browser; there are no CDN/runtime dependencies. Markdown and library.json are the editable sources. These local tools rebuild the study shell and MathML from the existing evidence exports; they do not download research, implement metrics or regenerate the SQLite/evidence explorer.

For a rebuild, install Node.js plus `marked`17.0.5 from package.json and Python plus latex2mathml3.81.1 from requirements.txt in an isolated environment. Run from this directory:

```text
python typeset-math.py
node build-study.mjs
python brand-docs.py
python check-docs.py
```

The shell assets are included under ../assets. If changing canonical evidence records, regenerate the complete schema-v1 evidence explorer/SQLite through the owning research-library toolchain before running check-docs; the saved exports remain usable without that authoring toolchain. A DOC_SHELL_SOURCE override can consume maintained shared shell assets; MARKED_MODULE can identify an already-installed Marked module. No host paths or credentials are required. The source snapshot includes a generated math-markdown.json for inspection; typeset-math.py rebuilds it.

The check script requires Git, this project's baseline refs and source/assets checkout. Its saved receipt does not prove browser or GPU validation. Record UI tests separately. Renderer builds need upstream's actual toolchain/dependencies.
