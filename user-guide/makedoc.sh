#!/bin/bash

NAME=user-guide
BIB=refs.bibtex

pandoc -s $NAME.txt --bibliography $BIB --latex-engine=xelatex \
       --include-in-header=header-includes.tex \
       -o $NAME.pdf

pandoc -s $NAME.txt --bibliography $BIB -o $NAME.html
