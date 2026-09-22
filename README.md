# 📄 Resume Vault

Canonical resume source and reusable project evidence for **Kartikay**. The vault deliberately publishes one base resume; job-specific variants are generated on demand in Job Mailer's Application Studio instead of being stored here.

## 🗂️ Folder structure

```
resume-vault/
├── research_engineer/     ← canonical AI Research Engineer base
│   ├── research-engineer.tex
│   ├── research-engineer.pdf
│   └── resume.json
├── projects/              ← reusable, evidence-backed project blocks
├── llm-profile.json       ← generated compact candidate context
└── .github/workflows/     ← auto-compile pipeline
```

**Invariant:** exactly one active `resume.json` must exist. The Pages build rejects zero or multiple active resumes. Job Mailer treats this record as the canonical base, ranks the independent project catalog for each job, injects the selected project pair, and then runs the normal factual tailoring flow.

## 🧱 Reusable project blocks

`projects/<project-id>/<project-id>.tex` contains one reusable LaTeX block per portfolio project. Its body uses the exact same `\resumeSubheading`, `\resumeItemListStart`, literal `\item {...}`, `\resumeItemListEnd`, and `\vspace{-2mm}` syntax as the active resumes. Repository evidence, role families, skills, bullet IDs, and per-bullet JD tags live in comments, so Job Mailer can rank or remove bullets without changing their resume-native LaTeX structure.

Each block is dual-purpose: it compiles by itself into a cropped PDF preview that mirrors the current resume typography and spacing, or becomes a direct drop-in entry when `\ResumeProjectMode` is defined inside the parent resume's project list. `projects/project-blob.sty` only supplies copies of the existing resume macros for standalone preview compilation.

```tex
\resumeSubHeadingListStart
\def\ResumeProjectMode{}
\input{projects/gogent/gogent.tex}
\resumeSubHeadingListEnd
```

The Pages build validates every source, publishes its compiled preview beside it, and generates a discovery catalog:

```text
https://kartikaysaxena.github.io/resume-vault/projects/index.json
https://kartikaysaxena.github.io/resume-vault/projects/<project-id>/<project-id>.tex
https://kartikaysaxena.github.io/resume-vault/projects/<project-id>/<project-id>.pdf
```

`manifest.json` exposes `project_catalog_url` and its SHA-256 digest, so consumers can discover and verify the catalog without hard-coding its path.

## 🔄 Auto-recompile workflow

A GitHub Actions workflow (`.github/workflows/compile.yml`) keeps each PDF in sync with its `.tex`:

- **Trigger:** any push that changes a `.tex` file, or a manual `workflow_dispatch` run.
- **Action:** compiles every changed `.tex` with **TeX Live 2025 + pdflatex** (`latexmk`) inside GitHub Actions — the same generation Overleaf uses, not latexonline.cc.
- **Page gate:** validates every active PDF and fails the build unless each resume is exactly one page.
- **Commit:** the freshly compiled `.pdf` is committed back into the same folder.
- **Profile:** on every TeX change, the workflow asks an OpenAI-compatible model for one factual JSON profile and commits it at the repository root.
- **Publish:** the canonical PDF and a validated `manifest.json` are deployed to **GitHub Pages**. TeX remains available from its pinned GitHub source revision rather than being copied into Pages.
- **Project catalog:** reusable project blocks are validated and deployed alongside the resume catalog for deterministic JD matching.
- **Result:** the PDF in a folder is always up-to-date with its `.tex`, and always reachable at the same shareable link.

### Static PDF URLs (GitHub Pages)
Each resume has a permanent URL derived from its folder + filename. It never changes across iterations:

```
https://kartikaysaxena.github.io/resume-vault/<folder>/<resume>.pdf
```

Canonical resume: `https://kartikaysaxena.github.io/resume-vault/research_engineer/research-engineer.pdf`

Catalog: `https://kartikaysaxena.github.io/resume-vault/manifest.json`

Candidate profile: `https://kartikaysaxena.github.io/resume-vault/llm-profile.json`

Project catalog: `https://kartikaysaxena.github.io/resume-vault/projects/index.json`

Set the repository Actions secret `PROFILE_LLM_API_KEY`. Optional Actions variables `PROFILE_LLM_MODEL` and `PROFILE_LLM_BASE_URL` select another OpenAI-compatible model or endpoint; the defaults are `deepseek/deepseek-chat` through OpenRouter. Profile generation consumes tokens only when a TeX source changes (or the workflow is run manually). Job Mailer fetches the published result instead of making a separate profile-generation call.

> CI uses a full TeX Live 2025 image, so package availability matches a current Overleaf `pdflatex` project. The template still uses `fontawesome` (v4) rather than `fontawesome5`; both are present in TeX Live 2025.


## ➕ How to update the resume system

1. **Update the canonical base:** edit `research_engineer/research-engineer.tex`, commit, and push. The workflow recompiles and updates its PDF automatically.
2. **Add project evidence:** add a validated block under `projects/<project-id>/`. Application Studio can then rank and inject it without adding another stored resume variant.
3. **Generate a role-specific variant:** open a job in Application Studio. It starts from the canonical base, selects two reusable projects, applies factual JD-aware edits, compiles a one-page PDF, and stores that generated application artifact outside this vault.

> Note: the PDF is a **build artifact** — always edit the `.tex`, never the `.pdf`. The workflow will regenerate the PDF from source.

## 🧑‍💻 For agents (and humans)

- **Always edit `.tex` files**, never the committed `.pdf`.
- Keep the canonical `resume.json` skills factual: Job Mailer uses this list as the allow-list for deterministic ATS keyword additions.
- The workflow keeps PDFs in sync — you usually don't need to compile locally.
- If a resume uses custom classes/packages, ensure they're referenced correctly or committed alongside (this template is self-contained and uses standard TeX packages: `tcolorbox`, `fontawesome5`, `hyperref`, `tabularx`, etc.).
- Do not add role-specific resume folders. Add reusable evidence to `projects/` and let Application Studio generate the variant.
