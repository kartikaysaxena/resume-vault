# 📄 Resume Vault

Central repository for **Kartikay's** resumes. Each supported role has its own folder containing the **LaTeX source** (`.tex`) and its **compiled PDF**, plus placeholder folders for roles that aren't built yet.

## 🗂️ Folder structure

```
resume-vault/
├── software_engineer/     ← Software Engineer resume (live, auto-compiled)
│   ├── software-engineer.tex
│   └── software-engineer.pdf
├── research_engineer/     ← placeholder (no resume yet)
├── ml_engineer/           ← placeholder (no resume yet)
└── .github/workflows/     ← auto-compile pipeline
```

**Convention:** one folder per role. Each folder holds exactly one `.tex` source and the matching `.pdf` output, named after the folder (e.g. `software_engineer/software-engineer.tex` → `software-engineer.pdf`).

## 🔄 Auto-recompile workflow

A GitHub Actions workflow (`.github/workflows/compile.yml`) keeps each PDF in sync with its `.tex`:

- **Trigger:** any push that changes a `.tex` file (in any role folder), or a manual `workflow_dispatch` run.
- **Action:** compiles every changed `.tex` to PDF using a full **TeX Live (pdflatex)** image — the same compiler as Overleaf, so it tolerates the template's benign `Lonely \item` warnings that strict compilers like tectonic reject.
- **Commit:** the freshly compiled `.pdf` is committed back into the same folder.
- **Result:** the PDF in a folder is always up-to-date with its `.tex`.

## ➕ How to add / update a resume

1. **Edit an existing role:** edit `software_engineer/software-engineer.tex`, commit + push → the workflow recompiles and updates the PDF automatically. No need to compile locally.
2. **Add a new role:** create a folder (e.g. `data_engineer/`), drop in `data_engineer.tex`, push → the workflow picks up the new `.tex` and emits `data_engineer.pdf`.

> Note: the PDF is a **build artifact** — always edit the `.tex`, never the `.pdf`. The workflow will regenerate the PDF from source.

## 🧑‍💻 For agents (and humans)

- **Always edit `.tex` files**, never the committed `.pdf`.
- The workflow keeps PDFs in sync — you usually don't need to compile locally.
- If a resume uses custom classes/packages, ensure they're referenced correctly or committed alongside (this template is self-contained and uses standard TeX packages: `tcolorbox`, `fontawesome5`, `hyperref`, `tabularx`, etc.).
- Role folders without a resume are placeholders — add the `.tex` when ready.
