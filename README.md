# How to Setup:

1. Download Tesseract from
	- https://tesseract-ocr.github.io/tessdoc/Installation.html
	- https://github.com/UB-Mannheim/tesseract/wiki
2. Download Languages `*.traineddata` (Optional)
	- https://github.com/tesseract-ocr/tessdata
3. Move downloaded languages to the installed path `.../Tesseract-OCR/tessdata/`
4. Move your images `(.png, .jpg, .jpeg)` into `images/`
5. Update `settings.cfg` if needed
	- `TESSERACT_PATH`: Path to `tesseract.exe`
	- `TIMEOUT`: Timeout for OCR process, E.g. `<int>0`
	- `OUTPUT_TYPE`: `TEXT` or `PDF`
	- `LANG`: Any available languages, E.g. `eng`
	- `COMBINE`: Combine output into one file, E.g. `<bool>TRUE`
	- `CLEAR_OUTPUT`: Clear output folder before extraction, E.g. `<bool>TRUE`
	- `PRINT_TEXT`: Print output after each extraction, E.g. `<bool>TRUE`
6. Run `python OCR.py`
