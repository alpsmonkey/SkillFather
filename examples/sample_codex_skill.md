---
name: pdf-editor
description: This skill should be used when users ask to modify, rotate, or extract text from PDF files.
allowed-tools: Read, Write, Bash
---

# PDF Editor

This skill handles PDF file operations including rotation, text extraction, and modification.

## When to Use

- User asks to rotate a PDF page
- User wants to extract text from a PDF
- User needs to merge or split PDF files

## Instructions

1. First check the PDF file exists using `ls` or `Read`
2. For rotation: use `pdftotext` or Python's PyPDF2
3. For text extraction: use `pdftotext` command
4. Always verify the output before presenting to user

## Examples

To rotate a PDF:
```bash
pdftk input.pdf cat 1-endS output rotated.pdf
```

To extract text:
```bash
pdftotext input.pdf output.txt
```
