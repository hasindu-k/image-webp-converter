from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Event
from typing import Callable, Dict, Iterable, Optional

from PIL import Image, ImageOps


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


ProgressCallback = Callable[[Dict[str, object]], None]


def collect_images(input_folder: str | Path) -> list[Path]:
    """Collect supported image files from input folder and subfolders."""
    input_path = Path(input_folder)

    if not input_path.exists():
        raise FileNotFoundError(f"Input folder does not exist: {input_path}")

    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a folder: {input_path}")

    return [
        path
        for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def _prepare_image_mode(img: Image.Image) -> Image.Image:
    """
    Prepare image for WebP saving.

    Keeps alpha channel for transparent PNG images.
    Converts normal images to RGB.
    """
    if img.mode in ("RGBA", "LA") or "transparency" in img.info:
        return img.convert("RGBA")
    return img.convert("RGB")


def convert_single_image(
    image_path: Path,
    input_folder: Path,
    output_folder: Path,
    width: int,
    quality: int,
    suffix: str,
    skip_upscale: bool = True,
) -> tuple[bool, str]:
    """
    Convert one image to WebP while preserving folder structure.

    Returns:
        (success, message)
    """
    try:
        relative_parent = image_path.parent.relative_to(input_folder)
        output_subfolder = output_folder / relative_parent
        output_subfolder.mkdir(parents=True, exist_ok=True)

        output_name = f"{image_path.stem}-{suffix}.webp"
        output_path = output_subfolder / output_name

        with Image.open(image_path) as img:
            img = ImageOps.exif_transpose(img)
            img = _prepare_image_mode(img)

            if skip_upscale and img.width <= width:
                resized = img.copy()
            else:
                ratio = width / img.width
                height = max(1, int(img.height * ratio))
                resized = img.resize((width, height), Image.LANCZOS)

            resized.save(output_path, "WEBP", quality=quality, method=6)

        return True, f"Converted: {image_path} -> {output_path}"

    except Exception as exc:
        return False, f"Error converting {image_path}: {exc}"


def convert_images(
    input_folder: str | Path,
    output_folder: str | Path,
    width: int = 800,
    quality: int = 70,
    suffix: str = "medium",
    max_workers: int = 8,
    skip_upscale: bool = True,
    callback: Optional[ProgressCallback] = None,
    stop_event: Optional[Event] = None,
) -> dict[str, int]:
    """
    Convert all supported images in a folder tree to WebP.

    callback receives dictionaries like:
        {"type": "start", "total": 10}
        {"type": "progress", "done": 1, "total": 10, "success": True, "message": "..."}
        {"type": "finish", "converted": 9, "failed": 1, "skipped": 0}
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)

    if width <= 0:
        raise ValueError("Width must be greater than 0")

    if not 1 <= quality <= 100:
        raise ValueError("Quality must be between 1 and 100")

    if max_workers <= 0:
        raise ValueError("Max workers must be greater than 0")

    suffix = suffix.strip() or "medium"
    output_path.mkdir(parents=True, exist_ok=True)

    images = collect_images(input_path)
    total = len(images)

    converted = 0
    failed = 0
    skipped = 0
    done = 0

    if callback:
        callback({"type": "start", "total": total})

    if total == 0:
        if callback:
            callback(
                {
                    "type": "finish",
                    "converted": converted,
                    "failed": failed,
                    "skipped": skipped,
                }
            )
        return {"converted": converted, "failed": failed, "skipped": skipped}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        for image_path in images:
            if stop_event and stop_event.is_set():
                skipped += 1
                continue

            futures.append(
                executor.submit(
                    convert_single_image,
                    image_path,
                    input_path,
                    output_path,
                    width,
                    quality,
                    suffix,
                    skip_upscale,
                )
            )

        for future in as_completed(futures):
            if stop_event and stop_event.is_set():
                skipped += 1
                continue

            success, message = future.result()
            done += 1

            if success:
                converted += 1
            else:
                failed += 1

            if callback:
                callback(
                    {
                        "type": "progress",
                        "done": done,
                        "total": total,
                        "success": success,
                        "message": message,
                    }
                )

    if callback:
        callback(
            {
                "type": "finish",
                "converted": converted,
                "failed": failed,
                "skipped": skipped,
            }
        )

    return {"converted": converted, "failed": failed, "skipped": skipped}