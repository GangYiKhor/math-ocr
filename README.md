# OCR-Math

An OCR application to extract text and/or mathematical expressions from images, which can be exported in `.docx` format for easy copy paste process.

They can also be copied one by one and paste into MS Words as Equation/Text.

## Environments:

- `Ubuntu 24.04.1 LTS`
- `Python 3.12`
- `Node v23.10.0`

## How to Setup:

### 1. Clone this repository

```bash
git clone https://github.com/GangYiKhor/math-ocr.git
cd math-ocr
```

### 2. Linux prerequisites

```bash
sudo apt-get update
sudo apt-get install gcc
sudo apt-get install protobuf-compiler libprotoc-dev
```

### 3. Install `Python` and packages

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-dev
sudo apt install pipx
pipx ensurepath
pipx install virtualenv
# May need to restart for virtualenv to be in PATH

virtualenv -p /usr/bin/python3.12 .venv
source .venv/bin/activate

# Install ONNX
export CMAKE_ARGS="-DONNX_USE_PROTOBUF_SHARED_LIBS=ON"
pip install onnx

# Optional, only install CPU version of PyTorch
pip install -r requirements-pytorch-cpu-linux.txt

pip install -r requirements.txt
```

### 4. Install `NVM`, `Node` and modules

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

nvm install
nvm use
npm --prefix ./frontend install
```

### 5. Install Tesseract and languages

```bash
# Refer to https://tesseract-ocr.github.io/tessdoc/Installation.html for Windows
sudo apt install tesseract-ocr

# Download Malay language
wget https://raw.githubusercontent.com/tesseract-ocr/tessdata/refs/heads/main/msa.traineddata
sudo mv msa.traineddata /usr/share/tesseract-ocr/5/tessdata/
```

### 6. Create .env File

```bash
cp .env.template .env
# Update env if needed
```

### 7. Create user _(Optional if WITH_AUTH is false)_

```bash
python backend/createsuperuser.py
```

### 8. User management _(Optional if WITH_AUTH is false)_

#### Change pasword

```bash
python backend/changepassword.py
```

#### Activate user accounts

```bash
python backend/activateuser.py
```

### 9. Run development server

- Two servers required
- You may also run debug in `VSCode` for both servers
- Server will be started at http://localhost:8000

```bash
# Python server
fastapi dev backend/main.py

# Vue server
npm --prefix ./frontend run dev
```

## How to Run Production Server

### Run Makefile script

```bash
make run/prod
```

#### === OR ===

### 1. Build frontend

```bash
npm --prefix ./frontend run build
```

### 2. Run FastAPI server

```bash
python startserver.py
```
