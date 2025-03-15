# OCR-Math

An OCR application to extract text and/or mathematical expressions from images, which can be exported in `.docx` format for easy copy paste process.

Copy function does not work well for mathematical expressions yet, you need to paste the copied mathml to `Notepad`, then copy them again _**(block by block)**_ and paste on `Microsoft Words` to make it work.

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
7. Define `TESSERACT_PATH` in `.env` (Refer to `.env.template`)
8. Create a user by running `python backend/createuser.py`
   - You may change password using `python backend/changepassword.py`

## How to Run

```bash
cd frontend
npm run build
cd ..
fastapi run backend/main.py
# Or run debug session `FastAPI Dev` in VSCode
# Might take some time to start up due to PyTorch model loading
```
