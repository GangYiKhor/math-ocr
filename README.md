# OCR-Math

An OCR application to extract text and/or mathematical expressions from images, which can be exported as MS `.docx` format for easy copy paste process

## How to Setup:

1. Clone this repository
2. Run `pip install -r requirements.txt`
3. Run `cd frontend && npm install`
4. Download Tesseract from
   - https://tesseract-ocr.github.io/tessdoc/Installation.html
   - https://github.com/UB-Mannheim/tesseract/wiki
5. Download Languages `*.traineddata` (Optional)
   - https://github.com/tesseract-ocr/tessdata
6. Move downloaded languages to the installed path `.../Tesseract-OCR/tessdata/`
7. Move/Copy `Tesseract-OCR/` into this repository, besides `backend`/`frontend` directory
8. Modify `TESSERACT_PATH` in `backend/settings.py`

## How to Run (Dev)

```bash
cd frontend
npm run build
cd ..
fastapi dev backend/main.py
# Or run debug session `FastAPI Dev` in VSCode
# Might take some time to start up due to PyTorch model loading
```
