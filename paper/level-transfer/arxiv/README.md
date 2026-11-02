# arXiv version

`paper_arxiv.md` is the text. `main.tex` is generated from it, and together with `figures/fig6_e21_transfer.png` it is
the source uploaded to arXiv. `paper_arxiv.pdf` is that source built with pdflatex (TeX Live 2026, two passes).

Rebuild from this folder:

    pandoc paper_arxiv.md -s -o main.tex --shift-heading-level-by=-1 -H header.tex -V geometry:margin=1in -V fontsize=11pt -V colorlinks=true -V urlcolor=blue -V linkcolor=black
    printf '%s\n' '\pdfoutput=1' | cat - main.tex > main.tmp && mv main.tmp main.tex
    pdflatex main.tex && pdflatex main.tex

How it differs from the Paper Track text in `../paper/`:
- The title names ARC-AGI-3 and the finding.
- The abstract and section 4 say that M1 is a verbatim replay, and give the 452 pairs whose budget covers the next human solution.
- Section 4 adds session-cluster and game-level intervals for M2 and M3.
- Section 5a adds the other memory-on seeds.
- Section 1 defines ARC-AGI-3.
- Section 5b adds the model input, the sampling settings and the draw plan with its 26 October change.
- Section 7 adds the contamination, agent-view and outcome limits.
- Section 2 dates the novelty search and cites two October papers, as [17] and [18].
- The Disclosure adds competing interests, funding and data rights.
- Code and data cites fixed commits.
