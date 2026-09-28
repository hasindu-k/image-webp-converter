# Image to WebP Converter Desktop App

A simple desktop app for Windows and Ubuntu/Linux to convert JPG, JPEG, and PNG images into WebP format.

## Features

- Select input folder
- Optionally select a separate output folder
- Save converted images in the input folder by default
- Preserve subfolder structure
- Resize images by width while maintaining aspect ratio
- Convert to WebP
- Control output quality
- Add suffix such as `medium`
- Use multithreading for faster conversion
- Progress bar and conversion log
- Build as a Windows `.exe`

## Project Structure

```text
image_webp_converter_desktop/
├── app.py
├── converter.py
├── requirements.txt
├── build_exe.bat
└── README.md
```

## Setup on Windows

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies and run the app:

```bash
python -m pip install -r requirements.txt
python app.py
```

## Setup on Ubuntu/Linux

Install Python, the virtual-environment tools, and Tkinter:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-tk
```

Clone or download this project, then create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the Python dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

To leave the virtual environment when you are finished, run:

```bash
deactivate
```

By default, converted images are saved alongside the source images in the input
folder. Enable **Use a separate output folder** in the app to choose a different
destination while preserving the input folder's subfolder structure.

The initial input folder is `~/Downloads/convert-images`. The app remembers the
input folder when you browse, begin a conversion, or close the app, then restores
it the next time the app starts.

## Build a Windows EXE

Run:

```bash
build_exe.bat
```

After building, check the `dist` folder.

```text
dist/ImageWebPConverter.exe
```

## Build a Linux Executable

On Ubuntu/Linux, with the virtual environment activated, run:

```bash
pyinstaller --onefile --windowed --name ImageWebPConverter app.py
```

The executable will be created at:

```text
dist/ImageWebPConverter
```

## Recommended Settings

```text
Width: 800
Quality: 70
Suffix: medium
Threads: 8
```

## Notes

- The app supports `.jpg`, `.jpeg`, and `.png`.
- Transparent PNG files are saved with transparency when possible.
- Small images are not enlarged by default.
- Output files are saved as:

```text
original-name-medium.webp
```
