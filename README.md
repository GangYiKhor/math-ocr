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

1. Start Vue Dev server

```bash
cd frontend
npm run dev
```

2. Start FastAPI server
```bash
fastapi dev backend/main.py
```

3. Visit the page at http://localhost:8000

## How to Run Production Server

1. Build frontend

```bash
cd frontend
npm run build
```

2. Run FastAPI server

```bash
fastapi run backend/main.py
```
