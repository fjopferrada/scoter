#!/bin/bash

NAME=user-guide
BIB=refs.bibtex
FORMAT=markdown

COMMON_OPTS="-f $FORMAT --bibliography $BIB \
-s $NAME.txt --number-sections --csl=harvard1.csl"

pandoc $COMMON_OPTS \
       --latex-engine=xelatex \
       --include-in-header=header-includes.tex \
       -o $NAME.pdf

pandoc $COMMON_OPTS --self-contained -o $NAME.html
