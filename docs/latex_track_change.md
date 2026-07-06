# Clean-up LaTeX Track Changes

## Remove TrackChanges

If you have track change commands from the `TrackChanges` package (not the `changes` package), the commands can be removed by:

1. Copy the entire Overleaf (or latex) folder to `PythonPackge` under `trackchanges` folder. For the command above to work, copy entire latex folder under `/trackchanges-0.7.0/PythonPackage/` folder.    Confirm you have `acceptchanges.py` in a folder above your latex files.  
2. Run `Terminal` and activate `python v 2.7`. Note that `acceptchanges.py` works only with `python v2.7`.
3. Compile main tex file and make pdf to keep an original tracked version in PDF file.
4. Rename all the tex files to be cleaned up.  `acceptchanges.py` does not automatically deal with `\input{}` or `\include{}` files.  So I have to process with `acceptchanges.py` all associated files individually.  
```
mv 0-main-text.tex 0-main-text-old.tex
```
5. Run the following command to clean up.
```
python ../acceptchanges.py -c -n --infile=0-main.tex --outfile=0-main-no-track.tex
```
I convert the code to python 3 using `2to3`.  Now in a python3 environment:
```
python ../acceptchanges3.py -c -n --infile=0-main.tex --outfile=0-main-no-track.tex
```

- If the command above does not change any, please consider remove all the commented parts using arxiv_latex_cleaner first.

## Remove Changes

For latex `changes` package was used for track change, use `pyMergeChanges.py`.  

```
python ../pyMergeChanges.py -a input.tex output.tex # python 3
```

## Remove comments and organize files for submission

Under the `base` environment of `anaconda`, I installed `arxiv_latex_cleaner` (https://github.com/google-research/arxiv-latex-cleaner).

```
arxiv_latex_cleaner Hydrogen_FeS_paper/ --im_size 500
```

- This will create organized package in a new folder, `Hydrogen_FeS_paper_arXiv`.  
- `arxiv_latex_cleaner` seems to know how to deal with `\include{}` and `\input{}`.  It also deals well with `bibunits`.  

