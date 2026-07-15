import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote


# ==================================================================
# Configuration
# ==================================================================

PROJECT_ROOT = Path(r"D:\react-app-oct\txta")

IMAGE_SOURCE_ROOT = PROJECT_ROOT / "brahma"

IMAGECLOUD_ROOT = PROJECT_ROOT / "imagecloud"

INPUT_JSON = (
    IMAGECLOUD_ROOT
    / "output"
    / "imageCloud.json"
)

PUBLIC_IMAGE_ROOT = (
    PROJECT_ROOT
    / "public"
    / "imagecloud"
)

OUTPUT_JS = (
    PROJECT_ROOT
    / "src"
    / "data"
    / "imageCloud.js"
)

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
}


# ==================================================================
# Helpers
# ==================================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(file_path: Path) -> dict[str, Any]:
    if not file_path.is_file():
        raise FileNotFoundError(
            f"Input JSON was not found:\n{file_path}\n\n"
            "Run analyze_images.py first."
        )

    try:
        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid JSON in:\n{file_path}\n\n{error}"
        ) from error

    if not isinstance(data, dict):
        raise RuntimeError(
            "imageCloud.json must contain a JSON object."
        )

    images = data.get("images")

    if not isinstance(images, list):
        raise RuntimeError(
            "imageCloud.json must contain an 'images' array."
        )

    return data


def clean_relative_path(value: str) -> str:
    """
    Normalize stored relative paths and block directory traversal.
    """

    normalized = value.replace("\\", "/").strip()

    while normalized.startswith("/"):
        normalized = normalized[1:]

    parts = [
        part
        for part in normalized.split("/")
        if part not in {"", "."}
    ]

    if ".." in parts:
        raise ValueError(
            f"Unsafe relative path: {value}"
        )

    if not parts:
        raise ValueError(
            "Image relativePath cannot be empty."
        )

    return "/".join(parts)


def create_public_url(relative_path: str) -> str:
    """
    URL-encode each path component without encoding slashes.
    """

    encoded_parts = [
        quote(part, safe="")
        for part in relative_path.split("/")
    ]

    return "/imagecloud/" + "/".join(encoded_parts)


def validate_text_field(
    record: dict[str, Any],
    field_name: str,
) -> str:
    value = record.get(field_name)

    if not isinstance(value, str):
        raise ValueError(
            f"'{field_name}' must be text."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"'{field_name}' cannot be empty."
        )

    return value


def normalize_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError(
            "Each image record must be an object."
        )

    relative_path = clean_relative_path(
        validate_text_field(
            record,
            "relativePath",
        )
    )

    source_file = (
        IMAGE_SOURCE_ROOT
        / Path(relative_path)
    )

    source_file = source_file.resolve()

    try:
        source_file.relative_to(
            IMAGE_SOURCE_ROOT.resolve()
        )
    except ValueError as error:
        raise ValueError(
            f"Image points outside brahma folder: "
            f"{relative_path}"
        ) from error

    if not source_file.is_file():
        raise FileNotFoundError(
            f"Referenced image was not found:\n"
            f"{source_file}"
        )

    if source_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image extension: "
            f"{source_file.suffix}"
        )

    image_id = record.get("id")

    if not isinstance(image_id, str) or not image_id.strip():
        raise ValueError(
            f"Record for {relative_path} has no valid id."
        )

    title = validate_text_field(record, "title")
    category = validate_text_field(record, "category")
    alt = validate_text_field(record, "alt")
    sha256 = validate_text_field(record, "sha256")

    return {
        "id": image_id.strip(),
        "fileName": source_file.name,
        "relativePath": relative_path,
        "src": create_public_url(relative_path),
        "title": title,
        "category": category,
        "alt": alt,
        "width": record.get("width"),
        "height": record.get("height"),
        "sizeBytes": record.get("sizeBytes"),
        "mimeType": record.get("mimeType"),
        "sha256": sha256,
        "createdAt": record.get("createdAt"),
        "updatedAt": record.get("updatedAt"),
    }


def copy_image(
    relative_path: str,
) -> None:
    source_file = (
        IMAGE_SOURCE_ROOT
        / Path(relative_path)
    )

    destination_file = (
        PUBLIC_IMAGE_ROOT
        / Path(relative_path)
    )

    destination_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        source_file,
        destination_file,
    )


def remove_empty_directories(
    root: Path,
) -> None:
    if not root.exists():
        return

    directories = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_dir()
        ),
        key=lambda path: len(path.parts),
        reverse=True,
    )

    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            pass


def remove_stale_public_images(
    expected_relative_paths: set[str],
) -> int:
    if not PUBLIC_IMAGE_ROOT.exists():
        return 0

    removed = 0

    for file_path in PUBLIC_IMAGE_ROOT.rglob("*"):
        if not file_path.is_file():
            continue

        relative_path = file_path.relative_to(
            PUBLIC_IMAGE_ROOT
        ).as_posix()

        if relative_path not in expected_relative_paths:
            file_path.unlink()
            removed += 1

    remove_empty_directories(PUBLIC_IMAGE_ROOT)

    return removed


def write_javascript(
    records: list[dict[str, Any]],
    source_metadata: dict[str, Any],
) -> None:
    OUTPUT_JS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    categories = sorted(
        {
            record["category"]
            for record in records
        },
        key=str.casefold,
    )

    payload = {
        "generatedAt": utc_now(),
        "sourceGeneratedAt": source_metadata.get(
            "generatedAt"
        ),
        "model": source_metadata.get("model"),
        "totalImages": len(records),
        "categories": categories,
        "images": records,
    }

    json_text = json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    )

    javascript = f"""/*
 * AUTO-GENERATED FILE.
 *
 * Do not edit this file manually.
 * Generated by:
 * imagecloud/generate_imageCloud_js.py
 */

const imageCloudData = {json_text};

export const imageCloudImages = imageCloudData.images;
export const imageCloudCategories = imageCloudData.categories;
export const imageCloudMetadata = {{
  generatedAt: imageCloudData.generatedAt,
  sourceGeneratedAt: imageCloudData.sourceGeneratedAt,
  model: imageCloudData.model,
  totalImages: imageCloudData.totalImages,
}};

export default imageCloudData;
"""

    temporary_file = OUTPUT_JS.with_suffix(
        ".js.tmp"
    )

    temporary_file.write_text(
        javascript,
        encoding="utf-8",
    )

    temporary_file.replace(OUTPUT_JS)


# ==================================================================
# Generation
# ==================================================================

def generate(
    clean: bool,
) -> int:
    database = load_json(INPUT_JSON)

    source_records = database["images"]

    normalized_records: list[dict[str, Any]] = []
    failed_records = 0

    print("=" * 80)
    print("IMAGE CLOUD — REACT DATA GENERATOR")
    print("=" * 80)
    print(f"Input JSON    : {INPUT_JSON}")
    print(f"Image source  : {IMAGE_SOURCE_ROOT}")
    print(f"Public images : {PUBLIC_IMAGE_ROOT}")
    print(f"Output JS     : {OUTPUT_JS}")
    print(f"JSON records  : {len(source_records)}")
    print("=" * 80)

    for index, record in enumerate(
        source_records,
        start=1,
    ):
        try:
            normalized = normalize_record(record)
            normalized_records.append(normalized)

            print(
                f"[{index}/{len(source_records)}] "
                f"VALID: {normalized['relativePath']}"
            )

        except Exception as error:
            failed_records += 1

            record_name = (
                record.get("relativePath", "unknown")
                if isinstance(record, dict)
                else "invalid record"
            )

            print(
                f"[{index}/{len(source_records)}] "
                f"FAILED: {record_name}"
            )
            print(
                f"    {type(error).__name__}: {error}"
            )

    if failed_records:
        print("\nGeneration stopped.")
        print(
            f"{failed_records} invalid record(s) found."
        )
        return 1

    normalized_records.sort(
        key=lambda item: (
            item.get("updatedAt") or "",
            item["title"].casefold(),
        ),
        reverse=True,
    )

    PUBLIC_IMAGE_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    expected_paths = {
        record["relativePath"]
        for record in normalized_records
    }

    if clean:
        stale_count = remove_stale_public_images(
            expected_paths
        )
    else:
        stale_count = 0

    for index, record in enumerate(
        normalized_records,
        start=1,
    ):
        copy_image(record["relativePath"])

        print(
            f"[{index}/{len(normalized_records)}] "
            f"COPIED: {record['relativePath']}"
        )

    write_javascript(
        normalized_records,
        database,
    )

    categories = sorted(
        {
            record["category"]
            for record in normalized_records
        },
        key=str.casefold,
    )

    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(
        f"Images copied       : "
        f"{len(normalized_records)}"
    )
    print(
        f"Stale images removed: {stale_count}"
    )
    print(
        f"Categories generated: {len(categories)}"
    )
    print(f"Generated JS        : {OUTPUT_JS}")
    print("=" * 80)

    return 0


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate React image-cloud data and copy "
            "gallery images into Vite's public directory."
        )
    )

    parser.add_argument(
        "--no-clean",
        action="store_true",
        help=(
            "Do not remove stale files from "
            "public/imagecloud."
        ),
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    exit_code = generate(
        clean=not arguments.no_clean
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()