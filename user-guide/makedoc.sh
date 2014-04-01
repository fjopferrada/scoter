#!/bin/bash

NAME=user-guide
BIB=refs.bibtex
FORMAT=markdown

COMMON_OPTS="-f $FORMAT --bibliography $BIB \
-s $NAME.txt --number-sections --csl=harvard1.csl"

LATEX_OPTS="--template=template.tex \
--include-in-header=header-includes.tex \
--variable fontsize=11pt"

pandoc $COMMON_OPTS $LATEX_OPTS \
       --latex-engine=xelatex \
       -o $NAME.pdf

## LaTeX source output can be useful for diagnosing problems.
# 
# pandoc $COMMON_OPTS $LATEX_OPTS \
#        -t latex \
#        -o $NAME.tex

pandoc $COMMON_OPTS --self-contained -o $NAME.html
