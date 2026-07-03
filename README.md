# Image to WebP Converter Desktop App

A simple Windows desktop app to convert JPG, JPEG, and PNG images into WebP format.

## Features

- Select input folder
- Select output folder
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

## Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python app.py
```

## Build EXE

Run:

```bash
build_exe.bat
```

After building, check the `dist` folder.

```text
dist/ImageWebPConverter.exe
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