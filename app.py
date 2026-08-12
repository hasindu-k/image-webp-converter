from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from converter import convert_images


APP_TITLE = "Image to WebP Converter"


class ImageConverterApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("850x620")
        self.minsize(760, 560)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.use_output_folder_value = tk.BooleanVar(value=False)
        self.width_value = tk.StringVar(value="800")
        self.quality_value = tk.StringVar(value="70")
        self.suffix_value = tk.StringVar(value="")
        self.workers_value = tk.StringVar(value="8")
        self.skip_upscale_value = tk.BooleanVar(value=True)

        self.message_queue: queue.Queue[dict[str, object]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()

        self._build_ui()
        self.after(100, self._process_queue)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Image to WebP Converter",
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        title.grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Convert JPG, JPEG, and PNG images to WebP while preserving subfolder structure.",
            text_color="gray",
        )
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=2, column=0, padx=24, pady=8, sticky="ew")
        folder_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(folder_frame, text="Input Folder").grid(
            row=0, column=0, padx=14, pady=12, sticky="w"
        )
        ctk.CTkEntry(folder_frame, textvariable=self.input_folder).grid(
            row=0, column=1, padx=8, pady=12, sticky="ew"
        )
        ctk.CTkButton(
            folder_frame, text="Browse", width=100, command=self.choose_input_folder
        ).grid(row=0, column=2, padx=14, pady=12)

        self.output_folder_checkbox = ctk.CTkCheckBox(
            folder_frame,
            text="Use a separate output folder",
            variable=self.use_output_folder_value,
            command=self.toggle_output_folder,
        )
        self.output_folder_checkbox.grid(
            row=1, column=0, padx=14, pady=12, sticky="w"
        )
        self.output_folder_entry = ctk.CTkEntry(
            folder_frame,
            textvariable=self.output_folder,
            placeholder_text="Converted images will be saved in the input folder",
            state="disabled",
        )
        self.output_folder_entry.grid(
            row=1, column=1, padx=8, pady=12, sticky="ew"
        )
        self.output_folder_button = ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=100,
            state="disabled",
            command=self.choose_output_folder,
        )
        self.output_folder_button.grid(row=1, column=2, padx=14, pady=12)

        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=3, column=0, padx=24, pady=8, sticky="ew")
        settings_frame.grid_columnconfigure((1, 3, 5, 7), weight=1)

        ctk.CTkLabel(settings_frame, text="Width").grid(
            row=0, column=0, padx=(14, 6), pady=14, sticky="w"
        )
        ctk.CTkEntry(settings_frame, textvariable=self.width_value, width=90).grid(
            row=0, column=1, padx=6, pady=14, sticky="ew"
        )

        ctk.CTkLabel(settings_frame, text="Quality").grid(
            row=0, column=2, padx=(14, 6), pady=14, sticky="w"
        )
        ctk.CTkEntry(settings_frame, textvariable=self.quality_value, width=90).grid(
            row=0, column=3, padx=6, pady=14, sticky="ew"
        )

        ctk.CTkLabel(settings_frame, text="Suffix").grid(
            row=0, column=4, padx=(14, 6), pady=14, sticky="w"
        )
        ctk.CTkEntry(settings_frame, textvariable=self.suffix_value, width=110).grid(
            row=0, column=5, padx=6, pady=14, sticky="ew"
        )

        ctk.CTkLabel(settings_frame, text="Threads").grid(
            row=0, column=6, padx=(14, 6), pady=14, sticky="w"
        )
        ctk.CTkEntry(settings_frame, textvariable=self.workers_value, width=80).grid(
            row=0, column=7, padx=(6, 14), pady=14, sticky="ew"
        )

        ctk.CTkCheckBox(
            settings_frame,
            text="Do not enlarge small images",
            variable=self.skip_upscale_value,
        ).grid(row=1, column=0, columnspan=3, padx=14, pady=(0, 14), sticky="w")

        actions_frame = ctk.CTkFrame(self)
        actions_frame.grid(row=4, column=0, padx=24, pady=8, sticky="nsew")
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_rowconfigure(2, weight=1)

        self.progress_label = ctk.CTkLabel(actions_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, padx=14, pady=(14, 4), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(actions_frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, padx=14, pady=8, sticky="ew")

        self.log_text = ctk.CTkTextbox(actions_frame, height=240)
        self.log_text.grid(row=2, column=0, padx=14, pady=8, sticky="nsew")
        self.log("Select folders and click Convert.")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=5, column=0, padx=24, pady=(8, 20), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)

        self.convert_button = ctk.CTkButton(
            button_frame,
            text="Convert Images",
            height=42,
            command=self.start_conversion,
        )
        self.convert_button.grid(row=0, column=1, padx=8, sticky="e")

        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Stop",
            height=42,
            fg_color="gray",
            state="disabled",
            command=self.stop_conversion,
        )
        self.stop_button.grid(row=0, column=2, padx=8, sticky="e")

        self.open_button = ctk.CTkButton(
            button_frame,
            text="Open Output Folder",
            height=42,
            state="disabled",
            command=self.open_output_folder,
        )
        self.open_button.grid(row=0, column=3, padx=8, sticky="e")

    def choose_input_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select input folder")
        if folder:
            self.input_folder.set(folder)

    def toggle_output_folder(self) -> None:
        state = "normal" if self.use_output_folder_value.get() else "disabled"
        self.output_folder_entry.configure(state=state)
        self.output_folder_button.configure(state=state)

    def choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder.set(folder)

    def validate_inputs(self) -> tuple[Path, Path, int, int, str, int] | None:
        input_folder_text = self.input_folder.get().strip()

        if not input_folder_text:
            messagebox.showerror("Invalid Input", "Please select an input folder.")
            return None

        input_folder = Path(input_folder_text)
        if not input_folder.exists() or not input_folder.is_dir():
            messagebox.showerror("Invalid Input", "Please select a valid input folder.")
            return None

        if self.use_output_folder_value.get():
            output_folder_text = self.output_folder.get().strip()
            if not output_folder_text:
                messagebox.showerror("Invalid Output", "Please select an output folder.")
                return None
            output_folder = Path(output_folder_text)
        else:
            output_folder = input_folder

        try:
            width = int(self.width_value.get())
            quality = int(self.quality_value.get())
            workers = int(self.workers_value.get())
        except ValueError:
            messagebox.showerror("Invalid Settings", "Width, quality, and threads must be numbers.")
            return None

        if width <= 0:
            messagebox.showerror("Invalid Width", "Width must be greater than 0.")
            return None

        if quality < 1 or quality > 100:
            messagebox.showerror("Invalid Quality", "Quality must be between 1 and 100.")
            return None

        if workers < 1 or workers > 32:
            messagebox.showerror("Invalid Threads", "Threads must be between 1 and 32.")
            return None

        suffix = self.suffix_value.get().strip()

        return input_folder, output_folder, width, quality, suffix, workers

    def start_conversion(self) -> None:
        validated = self.validate_inputs()
        if not validated:
            return

        input_folder, output_folder, width, quality, suffix, workers = validated

        self.stop_event.clear()
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting...")
        self.log_text.delete("1.0", "end")
        self.log("Conversion started...")

        self.convert_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.open_button.configure(state="disabled")

        self.worker_thread = threading.Thread(
            target=self._run_conversion,
            args=(input_folder, output_folder, width, quality, suffix, workers),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_conversion(
        self,
        input_folder: Path,
        output_folder: Path,
        width: int,
        quality: int,
        suffix: str,
        workers: int,
    ) -> None:
        try:
            convert_images(
                input_folder=input_folder,
                output_folder=output_folder,
                width=width,
                quality=quality,
                suffix=suffix,
                max_workers=workers,
                skip_upscale=self.skip_upscale_value.get(),
                callback=self.message_queue.put,
                stop_event=self.stop_event,
            )
        except Exception as exc:
            self.message_queue.put({"type": "error", "message": str(exc)})

    def stop_conversion(self) -> None:
        self.stop_event.set()
        self.log("Stop requested. Running tasks may finish before stopping.")
        self.stop_button.configure(state="disabled")

    def _process_queue(self) -> None:
        try:
            while True:
                message = self.message_queue.get_nowait()
                self._handle_message(message)
        except queue.Empty:
            pass

        self.after(100, self._process_queue)

    def _handle_message(self, message: dict[str, object]) -> None:
        message_type = message.get("type")

        if message_type == "start":
            total = int(message.get("total", 0))
            self.progress_label.configure(text=f"Found {total} image(s).")
            self.log(f"Found {total} image(s).")

            if total == 0:
                self.progress_bar.set(0)

        elif message_type == "progress":
            done = int(message.get("done", 0))
            total = int(message.get("total", 1))
            text = str(message.get("message", ""))

            self.progress_bar.set(done / total if total else 0)
            self.progress_label.configure(text=f"Processing {done}/{total}")
            self.log(text)

        elif message_type == "finish":
            converted = int(message.get("converted", 0))
            failed = int(message.get("failed", 0))
            skipped = int(message.get("skipped", 0))

            self.progress_bar.set(1 if converted or failed else 0)
            self.progress_label.configure(
                text=f"Finished. Converted: {converted}, Failed: {failed}, Skipped: {skipped}"
            )
            self.log(f"Finished. Converted: {converted}, Failed: {failed}, Skipped: {skipped}")

            self.convert_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.open_button.configure(state="normal")

            messagebox.showinfo(
                "Conversion Finished",
                f"Converted: {converted}\nFailed: {failed}\nSkipped: {skipped}",
            )

        elif message_type == "error":
            self.progress_label.configure(text="Error")
            self.log(f"Error: {message.get('message', '')}")

            self.convert_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

            messagebox.showerror("Error", str(message.get("message", "")))

    def open_output_folder(self) -> None:
        if self.use_output_folder_value.get():
            folder = self.output_folder.get().strip()
        else:
            folder = self.input_folder.get().strip()

        if not folder or not Path(folder).exists():
            messagebox.showerror("Folder Not Found", "Output folder does not exist.")
            return

        os.startfile(folder)

    def log(self, message: str) -> None:
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")


if __name__ == "__main__":
    app = ImageConverterApp()
    app.mainloop()
