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

## How to Run (Dev)

### Method 1 (Shell)

1. Run `fastapi dev backend/main.py`
2. Run `npm run dev` in `./frontend/`

### Method 2 (VSCode)

1. Run debug session for `FastAPI Dev` and `Vue Dev`
