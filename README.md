# 📄 Resume Vault

Central repository for **Kartikay's** resumes. Each supported role has its own folder containing the **LaTeX source** (`.tex`), its **compiled PDF**, and compact selection metadata in `resume.json`. Placeholder folders are ignored until their artifacts and metadata are ready.

## 🗂️ Folder structure

```
resume-vault/
├── software_engineer/     ← Software Engineer resume (live, auto-compiled)
│   ├── software-engineer.tex
│   ├── software-engineer.pdf
│   └── resume.json
├── research_engineer/     ← placeholder (no resume yet)
├── ml_engineer/           ← placeholder (no resume yet)
├── llm-profile.json      ← generated compact candidate context
└── .github/workflows/     ← auto-compile pipeline
```

**Convention:** one folder per role. `resume.json` declares its source, PDF, role families, skills, and short summary. Job Mailer uses that small record to select a variant without sending every complete résumé to an LLM.

## 🔄 Auto-recompile workflow

A GitHub Actions workflow (`.github/workflows/compile.yml`) keeps each PDF in sync with its `.tex`:

- **Trigger:** any push that changes a `.tex` file (in any role folder), or a manual `workflow_dispatch` run.
- **Action:** compiles every changed `.tex` with **TeX Live 2025 + pdflatex** (`latexmk`) inside GitHub Actions — the same generation Overleaf uses, not latexonline.cc.
- **Commit:** the freshly compiled `.pdf` is committed back into the same folder.
- **Profile:** on every TeX change, the workflow asks an OpenAI-compatible model for one factual JSON profile and commits it at the repository root.
- **Publish:** active PDFs and a validated `manifest.json` catalog are deployed to **GitHub Pages**. TeX remains available from its pinned GitHub source revision rather than being copied into Pages.
- **Result:** the PDF in a folder is always up-to-date with its `.tex`, and always reachable at the same shareable link.

### Static PDF URLs (GitHub Pages)
Each resume has a permanent URL derived from its folder + filename. It never changes across iterations:

```
https://kartikaysaxena.github.io/resume-vault/<folder>/<resume>.pdf
```

Example: `https://kartikaysaxena.github.io/resume-vault/software_engineer/software-engineer.pdf`

Catalog: `https://kartikaysaxena.github.io/resume-vault/manifest.json`

Candidate profile: `https://kartikaysaxena.github.io/resume-vault/llm-profile.json`

Set the repository Actions secret `PROFILE_LLM_API_KEY`. Optional Actions variables `PROFILE_LLM_MODEL` and `PROFILE_LLM_BASE_URL` select another OpenAI-compatible model or endpoint; the defaults are `deepseek/deepseek-chat` through OpenRouter. Profile generation consumes tokens only when a TeX source changes (or the workflow is run manually). Job Mailer fetches the published result instead of making a separate profile-generation call.

> CI uses a full TeX Live 2025 image, so package availability matches a current Overleaf `pdflatex` project. The template still uses `fontawesome` (v4) rather than `fontawesome5`; both are present in TeX Live 2025.


## ➕ How to add / update a resume

1. **Edit an existing role:** edit `software_engineer/software-engineer.tex`, commit + push → the workflow recompiles and updates the PDF automatically. No need to compile locally.
2. **Add a new role:** create a folder, add its `.tex`, compiled `.pdf`, and `resume.json`, then push. The workflow validates and publishes the active variant.

> Note: the PDF is a **build artifact** — always edit the `.tex`, never the `.pdf`. The workflow will regenerate the PDF from source.

## 🧑‍💻 For agents (and humans)

- **Always edit `.tex` files**, never the committed `.pdf`.
- The workflow keeps PDFs in sync — you usually don't need to compile locally.
- If a resume uses custom classes/packages, ensure they're referenced correctly or committed alongside (this template is self-contained and uses standard TeX packages: `tcolorbox`, `fontawesome5`, `hyperref`, `tabularx`, etc.).
- Role folders without a resume are placeholders — add the `.tex` when ready.
