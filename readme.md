# YouTube Thumbnail Downloader GUI

<p align="center">
  <img src="assets/AppPreviewV0.4.1.png" alt="YouTube Thumbnail Downloader GUI preview" width="100%">
</p>

<p align="center">
  <strong>Desktop app built with Python and Tkinter to download the best public YouTube thumbnail from a single video or an entire playlist.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#screenshots">Screenshots</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#supported-urls">Supported URLs</a> •
  <a href="#build-a-windows-exe">Build</a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-24292f">
  <img alt="GUI" src="https://img.shields.io/badge/GUI-Tkinter-5d8cff">
  <img alt="Version" src="https://img.shields.io/badge/Version-0.4.1-success">
</p>

## Overview

**YouTube Thumbnail Downloader GUI** is a lightweight desktop utility that downloads the best public thumbnail available for:

- a single YouTube video
- a full playlist
- Shorts links
- live links
- embedded video links
- shortened `youtu.be` links

The app does not download video files. It only fetches the public thumbnail image exposed by YouTube in the best format and quality it can find.

## AI Notice

This project was created with AI assistance during its design, implementation, and iteration.

## Features

- Modern Tkinter desktop interface
- `Auto`, `Single video`, and `Playlist` modes
- Automatic URL type detection when `Auto` is selected
- Best-thumbnail fallback order:
  - `maxresdefault`
  - `sddefault`
  - `hqdefault`
  - `mqdefault`
  - `default`
- Format priority:
  - `webp`
  - `jpg`
- Real-time progress bar and status text
- Live log panel
- Download counters:
  - total
  - processed
  - downloaded
  - skipped
- Optional overwrite mode
- Optional automatic folder opening when the job finishes
- Clean filenames with the YouTube video ID included
- Playlist items stored in a dedicated subfolder with numbered filenames
- Clean stop handling for long playlist jobs

## Screenshots

<p align="center">
  <img src="assets/AppPreviewV0.4.1.gif" alt="Application preview" width="90%">
</p>

## Project Structure

```text
.
├── assets/
│   ├── AppPreviewV0.4.1.gif
│   └── AppPreviewV0.4.1.png
├── CHANGELOG.txt
├── LICENSE
├── readme.md
├── script.py
└── script.spec
```

## Installation

### Requirements

- Python 3.10 or newer
- `tkinter`
- `requests`
- `yt-dlp`

Notes:

- Python 3.11+ is recommended.
- On Windows, `tkinter` is usually included with the official Python installer.
- On some Linux distributions, you may need to install a package such as `python3-tk` separately.

### Clone the repository

```bash
git clone https://github.com/PanzerSniper/youtube-thumbnail-downloader-gui.git
cd youtube-thumbnail-downloader-gui
```

### Install dependencies

```bash
python -m pip install -U requests yt-dlp
```

## Usage

Run the app:

```bash
python script.py
```

Then:

1. Paste a YouTube URL.
2. Select a mode: `Auto`, `Single video`, or `Playlist`.
3. Choose an output folder.
4. Click `Start`.

Default output folder:

```text
thumbnails_best/
```

If `Auto` cannot determine the URL type, switch to `Single video` or `Playlist` manually.

## Supported URLs

- `https://www.youtube.com/watch?v=...`
- `https://youtu.be/...`
- `https://www.youtube.com/shorts/...`
- `https://www.youtube.com/live/...`
- `https://www.youtube.com/embed/...`
- `https://www.youtube.com/playlist?list=...`
- `https://m.youtube.com/...`
- `https://music.youtube.com/...`

## Output Examples

### Single Video

```text
MyFolder/
└── Video Title [VIDEO_ID].webp
```

### Playlist

```text
MyFolder/
└── Playlist Title/
    ├── 001 - First Video Title [VIDEO_ID].webp
    ├── 002 - Second Video Title [VIDEO_ID].jpg
    └── 003 - Third Video Title [VIDEO_ID].webp
```

## Build a Windows `.exe`

Install PyInstaller:

```bash
python -m pip install -U pyinstaller
```

Build with the included spec file:

```bash
pyinstaller script.spec
```

The generated executable is written to:

```text
dist/script.exe
```

If you want a custom executable name, edit the `name=` field in `script.spec` before building.

## Changelog

Version history is available in [`CHANGELOG.txt`](./CHANGELOG.txt).

Current latest version documented in the project: `0.4.1`

## Contributing

Issues, bug reports, and pull requests are welcome.

## License

This project is released under the **MIT License**. See [`LICENSE`](./LICENSE).

## Author

- GitHub: [PanzerSniper](https://github.com/PanzerSniper)
- Repository: [youtube-thumbnail-downloader-gui](https://github.com/PanzerSniper/youtube-thumbnail-downloader-gui)
