# OCR-Math

An OCR application to extract text and/or mathematical expressions from images, which can be exported as MS `.docx` format for easy copy paste process

## How to Setup:
1. Clone this repository
2. Run `pip install -r requirements.txt`
3. Download Tesseract from
	- https://tesseract-ocr.github.io/tessdoc/Installation.html
	- https://github.com/UB-Mannheim/tesseract/wiki
4. Download Languages `*.traineddata` (Optional)
	- https://github.com/tesseract-ocr/tessdata
5. Move downloaded languages to the installed path `.../Tesseract-OCR/tessdata/`
6. Move `Tesseract-OCR/` into this repository
7. Move your images `(.png, .jpg, .jpeg)` into `images/`
8. Update `settings.cfg` if needed
	- `TIMEOUT`: Timeout for OCR process, E.g. `<int>0`
	- `LANG`: Any available languages, E.g. `eng`

## How to Run
### Method 1 (Python Script)
1. Edit image path in `ocr/p2t.py` (Formula) or `ocr/tesseract.py` (Text only)
2. Run `python ocr/p2t.py` or `python ocr/tesseract.py`

### Method 2 (FastAPI) [Incomplete]
1. Run `fastapi run backend/main.py`
2. Send request to `http://.../` (Does not accept param or file yet)
