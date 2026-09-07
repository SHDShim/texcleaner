# Cleaning LaTeX Track Changes

TeXCleaner supports documents marked with either `trackchanges.sty` or
`changes.sty`, as well as project preparation through
`arxiv-latex-cleaner`.

## Run the application

Use the repository's `docflow` conda environment:

```bash
conda activate docflow
python -m texcleaner
```

In the **Track Changes** tab, select a `.tex` file and leave **Cleaner** set
to **Auto detect**. Choose whether to keep the new or old text, whether to
remove annotations, and the desired output suffix. The source file is not
overwritten unless replacement is enabled explicitly.

In the **arXiv** tab, select the complete project folder and configure image,
PDF, bibliography, and output options. The cleaner creates a sibling output
folder.

## Bundled cleaners and licenses

The TrackChanges and Changes workflows use modified open-source cleaner
scripts included in this repository. Their original copyright notices,
licenses, and modification summaries are recorded in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and in the source-file
headers. The arXiv workflow invokes the separately installed Apache-2.0
`arxiv-latex-cleaner` dependency.
