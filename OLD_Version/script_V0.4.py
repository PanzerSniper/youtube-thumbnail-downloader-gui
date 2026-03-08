import os
import re
import queue
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from yt_dlp import YoutubeDL


APP_NAME = "YouTube Thumbnail Downloader"
APP_VERSION = "0.4"


def clean_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    return name.strip().rstrip(".")


def open_folder(path: Path):
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif os.name == "posix":
            subprocess.Popen(["xdg-open", str(path)])
        else:
            subprocess.Popen(["open", str(path)])
    except Exception as e:
        messagebox.showwarning("Open Folder", f"Unable to open the folder:\n{e}")


def extract_video_id_from_url(url: str) -> str | None:
    try:
        parsed = urlparse(url.strip())
        host = parsed.netloc.lower()
        path = parsed.path.strip("/")

        if "youtu.be" in host:
            parts = path.split("/")
            return parts[0] if parts and parts[0] else None

        if "youtube.com" in host or "music.youtube.com" in host or "m.youtube.com" in host:
            qs = parse_qs(parsed.query)

            if path == "watch":
                return qs.get("v", [None])[0]

            if path.startswith("shorts/"):
                parts = path.split("/")
                return parts[1] if len(parts) > 1 else None

            if path.startswith("live/"):
                parts = path.split("/")
                return parts[1] if len(parts) > 1 else None

            if path.startswith("embed/"):
                parts = path.split("/")
                return parts[1] if len(parts) > 1 else None

        return None
    except Exception:
        return None


def url_has_playlist(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
        qs = parse_qs(parsed.query)
        return "list" in qs or parsed.path.strip("/") == "playlist"
    except Exception:
        return False


def resolve_mode(url: str, selected_mode: str) -> str:
    if selected_mode == "Playlist":
        return "playlist"
    if selected_mode == "Single video":
        return "video"

    # Auto
    video_id = extract_video_id_from_url(url)
    has_playlist = url_has_playlist(url)

    if video_id:
        return "video"
    if has_playlist:
        return "playlist"

    raise ValueError("Unable to automatically determine whether the URL points to a video or a playlist.")


class ThumbnailDownloaderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1120x780")
        self.root.minsize(940, 680)
        self.root.configure(bg="#0f1115")

        self.queue = queue.Queue()
        self.is_running = False
        self.stop_requested = False
        self.last_output_dir = None

        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="Auto")
        self.output_dir_var = tk.StringVar(value=str(Path.cwd() / "thumbnails_best"))
        self.overwrite_var = tk.BooleanVar(value=False)
        self.open_folder_var = tk.BooleanVar(value=True)

        self.status_var = tk.StringVar(value="Ready.")
        self.progress_text_var = tk.StringVar(value="0 / 0")
        self.current_item_var = tk.StringVar(value="No task in progress.")

        self.total_items = 0
        self.processed_items = 0
        self.downloaded_items = 0
        self.skipped_items = 0

        self._configure_style()
        self._build_ui()
        self._poll_queue()

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background="#0f1115")
        style.configure("Card.TFrame", background="#171a21", relief="flat")
        style.configure("Header.TLabel", background="#0f1115", foreground="#f5f7fa", font=("Segoe UI", 18, "bold"))
        style.configure("SubHeader.TLabel", background="#0f1115", foreground="#a9b3c1", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#171a21", foreground="#f5f7fa", font=("Segoe UI", 11, "bold"))
        style.configure("TLabel", background="#0f1115", foreground="#e7ebf0")
        style.configure("Muted.TLabel", background="#171a21", foreground="#b4beca")
        style.configure("TEntry", fieldbackground="#0d1016", foreground="#f5f7fa", bordercolor="#30384a", insertcolor="#f5f7fa")
        style.map("TEntry", bordercolor=[("focus", "#5d8cff")])

        style.configure("TCombobox", fieldbackground="#0d1016", foreground="#f5f7fa", bordercolor="#30384a")
        style.map("TCombobox", bordercolor=[("focus", "#5d8cff")])

        style.configure("Primary.TButton", background="#5d8cff", foreground="white", borderwidth=0, padding=(14, 10))
        style.map("Primary.TButton", background=[("active", "#7aa0ff")])

        style.configure("Secondary.TButton", background="#242b38", foreground="#f5f7fa", borderwidth=0, padding=(12, 9))
        style.map("Secondary.TButton", background=[("active", "#2c3445")])

        style.configure("TCheckbutton", background="#171a21", foreground="#e7ebf0")
        style.map("TCheckbutton", background=[("active", "#171a21")])

        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#0d1016",
            background="#5d8cff",
            bordercolor="#0d1016",
            lightcolor="#5d8cff",
            darkcolor="#5d8cff"
        )

    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(self.root)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 8))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text=APP_NAME, style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Download the best public thumbnail available from a single video or a YouTube playlist.",
            style="SubHeader.TLabel"
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        main = ttk.Frame(self.root)
        main.grid(row=1, column=0, sticky="nsew", padx=20, pady=(4, 16))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        top_card = ttk.Frame(main, style="Card.TFrame", padding=18)
        top_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        top_card.grid_columnconfigure(1, weight=1)
        top_card.grid_columnconfigure(3, weight=0)

        ttk.Label(top_card, text="Settings", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 14))

        ttk.Label(top_card, text="YouTube URL:", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 8))
        self.url_entry = ttk.Entry(top_card, textvariable=self.url_var)
        self.url_entry.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(12, 0), pady=(0, 8), ipady=6)

        ttk.Label(top_card, text="Mode:", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 8))
        self.mode_combo = ttk.Combobox(
            top_card,
            textvariable=self.mode_var,
            values=["Auto", "Single video", "Playlist"],
            state="readonly"
        )
        self.mode_combo.grid(row=2, column=1, sticky="w", padx=(12, 10), pady=(0, 8))
        self.mode_combo.configure(width=20)

        ttk.Label(top_card, text="Output folder:", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(0, 8))
        self.dir_entry = ttk.Entry(top_card, textvariable=self.output_dir_var)
        self.dir_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(12, 10), pady=(0, 8), ipady=6)

        self.browse_btn = ttk.Button(top_card, text="Browse", style="Secondary.TButton", command=self.browse_output_dir)
        self.browse_btn.grid(row=3, column=3, sticky="e", pady=(0, 8))

        options_frame = ttk.Frame(top_card, style="Card.TFrame")
        options_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)
        options_frame.grid_columnconfigure(2, weight=1)

        ttk.Checkbutton(
            options_frame,
            text="Overwrite existing files",
            variable=self.overwrite_var
        ).grid(row=0, column=0, sticky="w")

        ttk.Checkbutton(
            options_frame,
            text="Open folder when finished",
            variable=self.open_folder_var
        ).grid(row=0, column=1, sticky="w")

        actions = ttk.Frame(top_card, style="Card.TFrame")
        actions.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(14, 0))
        actions.grid_columnconfigure(0, weight=0)
        actions.grid_columnconfigure(1, weight=0)
        actions.grid_columnconfigure(2, weight=1)
        actions.grid_columnconfigure(3, weight=0)

        self.start_btn = ttk.Button(actions, text="Start", style="Primary.TButton", command=self.start_download)
        self.start_btn.grid(row=0, column=0, sticky="w")

        self.stop_btn = ttk.Button(actions, text="Stop", style="Secondary.TButton", command=self.request_stop)
        self.stop_btn.grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.stop_btn.state(["disabled"])

        self.clear_log_btn = ttk.Button(actions, text="Clear log", style="Secondary.TButton", command=self.clear_log)
        self.clear_log_btn.grid(row=0, column=3, sticky="e")

        bottom = ttk.Frame(main)
        bottom.grid(row=1, column=0, sticky="nsew")
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_rowconfigure(1, weight=1)

        progress_card = ttk.Frame(bottom, style="Card.TFrame", padding=18)
        progress_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        progress_card.grid_columnconfigure(0, weight=1)

        ttk.Label(progress_card, text="Progress", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(progress_card, textvariable=self.current_item_var, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 8))

        progress_line = ttk.Frame(progress_card, style="Card.TFrame")
        progress_line.grid(row=2, column=0, sticky="ew")
        progress_line.grid_columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(progress_line, mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew")
        ttk.Label(progress_line, textvariable=self.progress_text_var, style="Muted.TLabel").grid(row=0, column=1, sticky="e", padx=(12, 0))

        stats_frame = ttk.Frame(progress_card, style="Card.TFrame")
        stats_frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        for c in range(4):
            stats_frame.grid_columnconfigure(c, weight=1)

        self.total_label = ttk.Label(stats_frame, text="Total : 0", style="Muted.TLabel")
        self.total_label.grid(row=0, column=0, sticky="w")

        self.processed_label = ttk.Label(stats_frame, text="Processed: 0", style="Muted.TLabel")
        self.processed_label.grid(row=0, column=1, sticky="w")

        self.ok_label = ttk.Label(stats_frame, text="Downloaded: 0", style="Muted.TLabel")
        self.ok_label.grid(row=0, column=2, sticky="w")

        self.skip_label = ttk.Label(stats_frame, text="Skipped: 0", style="Muted.TLabel")
        self.skip_label.grid(row=0, column=3, sticky="w")

        log_card = ttk.Frame(bottom, style="Card.TFrame", padding=18)
        log_card.grid(row=1, column=0, sticky="nsew")
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        ttk.Label(log_card, text="Log", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))

        log_container = tk.Frame(log_card, bg="#0d1016", highlightthickness=1, highlightbackground="#252c39")
        log_container.grid(row=1, column=0, sticky="nsew")
        log_container.grid_rowconfigure(0, weight=1)
        log_container.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_container,
            wrap="word",
            bg="#0d1016",
            fg="#d7deea",
            insertbackground="#d7deea",
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10)
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        log_scroll = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        footer = ttk.Frame(self.root)
        footer.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)

        ttk.Label(footer, textvariable=self.status_var, style="SubHeader.TLabel").grid(row=0, column=0, sticky="w")

    def browse_output_dir(self):
        selected = filedialog.askdirectory(title="Choose an output folder")
        if selected:
            self.output_dir_var.set(selected)

    def clear_log(self):
        self.log_text.delete("1.0", "end")

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def set_running_state(self, running: bool):
        self.is_running = running

        if running:
            self.start_btn.state(["disabled"])
            self.stop_btn.state(["!disabled"])
            self.browse_btn.state(["disabled"])
            self.url_entry.state(["disabled"])
            self.dir_entry.state(["disabled"])
            self.mode_combo.state(["disabled"])
        else:
            self.start_btn.state(["!disabled"])
            self.stop_btn.state(["disabled"])
            self.browse_btn.state(["!disabled"])
            self.url_entry.state(["!disabled"])
            self.dir_entry.state(["!disabled"])
            self.mode_combo.state(["readonly"])

    def update_stats(self):
        self.total_label.config(text=f"Total : {self.total_items}")
        self.processed_label.config(text=f"Processed: {self.processed_items}")
        self.ok_label.config(text=f"Downloaded: {self.downloaded_items}")
        self.skip_label.config(text=f"Skipped: {self.skipped_items}")
        self.progress["maximum"] = max(1, self.total_items)
        self.progress["value"] = self.processed_items
        self.progress_text_var.set(f"{self.processed_items} / {self.total_items}")

    def request_stop(self):
        if self.is_running:
            self.stop_requested = True
            self.status_var.set("Stop requested...")
            self.log("Stop request received. Finishing the current item...")

    def start_download(self):
        input_url = self.url_var.get().strip()
        output_dir = self.output_dir_var.get().strip()
        selected_mode = self.mode_var.get().strip()

        if not input_url:
            messagebox.showerror("Missing URL", "Please paste a YouTube URL.")
            return

        if not output_dir:
            messagebox.showerror("Missing folder", "Please choose an output folder.")
            return

        try:
            actual_mode = resolve_mode(input_url, selected_mode)
        except Exception as e:
            messagebox.showerror("Could not determine mode", str(e))
            return

        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Folder error", f"Unable to create/open the folder:\n{e}")
            return

        self.stop_requested = False
        self.total_items = 0
        self.processed_items = 0
        self.downloaded_items = 0
        self.skipped_items = 0
        self.last_output_dir = None

        self.current_item_var.set("Preparing...")
        self.status_var.set("Downloading...")
        self.update_stats()
        self.set_running_state(True)

        self.log("=" * 74)
        self.log(f"Download started | Version {APP_VERSION}")
        self.log(f"URL      : {input_url}")
        self.log(f"Mode     : {actual_mode}")
        self.log(f"Folder   : {output_dir}")
        self.log(f"Overwrite: {'Yes' if self.overwrite_var.get() else 'No'}")

        worker = threading.Thread(
            target=self._download_worker,
            args=(input_url, actual_mode, output_dir, self.overwrite_var.get(), self.open_folder_var.get()),
            daemon=True
        )
        worker.start()

    def _queue_put(self, kind: str, data=None):
        self.queue.put((kind, data))

    def _poll_queue(self):
        try:
            while True:
                kind, data = self.queue.get_nowait()

                if kind == "log":
                    self.log(str(data))

                elif kind == "status":
                    self.status_var.set(str(data))

                elif kind == "current_item":
                    self.current_item_var.set(str(data))

                elif kind == "set_total":
                    self.total_items = int(data)
                    self.update_stats()

                elif kind == "inc_processed":
                    self.processed_items += 1
                    self.update_stats()

                elif kind == "inc_ok":
                    self.downloaded_items += 1
                    self.update_stats()

                elif kind == "inc_skip":
                    self.skipped_items += 1
                    self.update_stats()

                elif kind == "done":
                    info = data or {}
                    self.last_output_dir = info.get("folder")
                    self.set_running_state(False)

                    if info.get("stopped"):
                        self.status_var.set("Download stopped.")
                        self.current_item_var.set("Processing stopped by user.")
                    else:
                        self.status_var.set("Download complete.")
                        self.current_item_var.set("Done.")

                    if info.get("open_folder") and info.get("folder"):
                        open_folder(Path(info["folder"]))

                elif kind == "error":
                    self.set_running_state(False)
                    self.status_var.set("Error.")
                    self.current_item_var.set("An error occurred.")
                    messagebox.showerror("Error", str(data))

        except queue.Empty:
            pass

        self.root.after(100, self._poll_queue)

    def _extract_playlist_info(self, url: str):
        ydl_opts = {
            "extract_flat": True,
            "skip_download": True,
            "ignoreerrors": True,
            "quiet": True,
            "noplaylist": False,
        }

        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _fetch_video_title(self, session: requests.Session, video_id: str) -> str:
        test_urls = [
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
            f"https://www.youtube.com/oembed?url=https://youtu.be/{video_id}&format=json",
        ]

        for api_url in test_urls:
            try:
                response = session.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    title = data.get("title")
                    if title:
                        return title
            except Exception:
                pass

        return f"video_{video_id}"

    def _resolve_targets(self, input_url: str, actual_mode: str, session: requests.Session):
        if actual_mode == "playlist":
            info = self._extract_playlist_info(input_url)
            if not info:
                raise RuntimeError("Unable to read the playlist.")

            playlist_title = clean_filename(info.get("title", "Playlist"))
            entries = [entry for entry in (info.get("entries") or []) if entry]

            items = []
            for index, entry in enumerate(entries, start=1):
                items.append({
                    "index": index,
                    "video_id": entry.get("id"),
                    "title": entry.get("title") or f"video_{index:03d}",
                })

            return {
                "collection_title": playlist_title,
                "save_in_subfolder": True,
                "items": items,
            }

        if actual_mode == "video":
            video_id = extract_video_id_from_url(input_url)
            if not video_id:
                raise RuntimeError("Unable to extract the video ID from the URL.")

            title = self._fetch_video_title(session, video_id)

            return {
                "collection_title": clean_filename(title),
                "save_in_subfolder": False,
                "items": [{
                    "index": 1,
                    "video_id": video_id,
                    "title": title,
                }],
            }

        raise RuntimeError("Invalid mode.")

    def _download_best_thumbnail(self, session: requests.Session, video_id: str, dest_base: Path):
        candidates = [
            ("maxres", f"https://i.ytimg.com/vi_webp/{video_id}/maxresdefault.webp", "webp"),
            ("maxres", f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg", "jpg"),
            ("sd",     f"https://i.ytimg.com/vi_webp/{video_id}/sddefault.webp", "webp"),
            ("sd",     f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg", "jpg"),
            ("hq",     f"https://i.ytimg.com/vi_webp/{video_id}/hqdefault.webp", "webp"),
            ("hq",     f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg", "jpg"),
            ("mq",     f"https://i.ytimg.com/vi_webp/{video_id}/mqdefault.webp", "webp"),
            ("mq",     f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg", "jpg"),
            ("default", f"https://i.ytimg.com/vi/{video_id}/default.jpg", "jpg"),
        ]

        for quality_label, url, ext in candidates:
            if self.stop_requested:
                return None, None

            try:
                response = session.get(url, stream=True, timeout=20)
                if response.status_code != 200:
                    response.close()
                    continue

                content_type = (response.headers.get("content-type") or "").lower()
                if "image" not in content_type:
                    response.close()
                    continue

                output_file = dest_base.with_suffix("." + ext)

                with open(output_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.stop_requested:
                            response.close()
                            try:
                                output_file.unlink(missing_ok=True)
                            except Exception:
                                pass
                            return None, None

                        if chunk:
                            f.write(chunk)

                response.close()
                return output_file, quality_label

            except Exception:
                continue

        return None, None

    def _download_worker(self, input_url: str, actual_mode: str, output_dir: str, overwrite: bool, open_folder_when_done: bool):
        try:
            local_processed = 0
            local_ok = 0
            local_skip = 0

            self._queue_put("status", "Analyzing...")
            self._queue_put("current_item", "Reading information...")
            self._queue_put("log", "Preparing network session...")

            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.youtube.com/",
            })

            self._queue_put("log", f"Resolved mode: {actual_mode}")
            target_info = self._resolve_targets(input_url, actual_mode, session)

            collection_title = target_info["collection_title"]
            save_in_subfolder = target_info["save_in_subfolder"]
            items = target_info["items"]

            if save_in_subfolder:
                final_dir = Path(output_dir) / collection_title
            else:
                final_dir = Path(output_dir)

            final_dir.mkdir(parents=True, exist_ok=True)

            self._queue_put("set_total", len(items))
            self._queue_put("log", f"Items detected: {len(items)}")
            self._queue_put("log", f"Final folder  : {final_dir}")

            for item in items:
                if self.stop_requested:
                    self._queue_put("log", "Stop requested by user.")
                    break

                index = item["index"]
                video_id = item["video_id"]
                title = item["title"] or f"video_{index:03d}"

                self._queue_put("current_item", f"Processing: {index}/{len(items)} | {title}")

                if not video_id:
                    self._queue_put("log", f"[SKIP] {index:03d} - {title} -> video ID not found")
                    local_processed += 1
                    local_skip += 1
                    self._queue_put("inc_processed")
                    self._queue_put("inc_skip")
                    continue

                safe_title = clean_filename(title)

                if actual_mode == "playlist":
                    base_name = f"{index:03d} - {safe_title} [{video_id}]"
                else:
                    base_name = f"{safe_title} [{video_id}]"

                dest_base = final_dir / base_name
                existing_files = list(final_dir.glob(base_name + ".*"))

                if existing_files and not overwrite:
                    self._queue_put("log", f"[SKIP] {existing_files[0].name} -> already exists")
                    local_processed += 1
                    local_skip += 1
                    self._queue_put("inc_processed")
                    self._queue_put("inc_skip")
                    continue

                if existing_files and overwrite:
                    for old_file in existing_files:
                        try:
                            old_file.unlink()
                        except Exception:
                            pass

                saved_file, quality_label = self._download_best_thumbnail(session, video_id, dest_base)

                if self.stop_requested:
                    break

                if saved_file:
                    self._queue_put("log", f"[OK]   {saved_file.name} -> quality {quality_label}")
                    local_processed += 1
                    local_ok += 1
                    self._queue_put("inc_processed")
                    self._queue_put("inc_ok")
                else:
                    self._queue_put("log", f"[SKIP] {title} -> no thumbnail downloaded")
                    local_processed += 1
                    local_skip += 1
                    self._queue_put("inc_processed")
                    self._queue_put("inc_skip")

            stopped = self.stop_requested

            self._queue_put("log", "-" * 74)
            self._queue_put("log", f"Mode          : {actual_mode}")
            self._queue_put("log", f"Name          : {collection_title}")
            self._queue_put("log", f"Folder        : {final_dir}")
            self._queue_put("log", f"Total         : {len(items)}")
            self._queue_put("log", f"Processed     : {local_processed}")
            self._queue_put("log", f"Downloaded    : {local_ok}")
            self._queue_put("log", f"Skipped       : {local_skip}")
            self._queue_put("log", "Processing finished.")

            self._queue_put("done", {
                "folder": str(final_dir),
                "open_folder": open_folder_when_done and not stopped,
                "stopped": stopped,
            })

        except Exception as e:
            self._queue_put("error", str(e))


def main():
    root = tk.Tk()
    app = ThumbnailDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
