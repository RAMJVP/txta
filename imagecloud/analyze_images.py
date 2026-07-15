import argparse
import hashlib
import json
import mimetypes
import os
import sys
import time
import traceback
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, UnidentifiedImageError

from prompt import IMAGE_PROMPT


# ==================================================================
# Configuration
# ==================================================================

PROJECT_ROOT = Path(r"D:\react-app-oct\txta")

IMAGE_ROOT = PROJECT_ROOT / "brahma"

SCRIPT_DIRECTORY = Path(__file__).resolve().parent

OUTPUT_DIRECTORY = SCRIPT_DIRECTORY / "output"

OUTPUT_JSON = OUTPUT_DIRECTORY / "imageCloud.json"

ENV_FILE = PROJECT_ROOT / ".env"

MODEL_NAME = "gemini-3.5-flash"

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

MAX_RETRIES = 3

RETRY_BASE_SECONDS = 3


# ==================================================================
# Utility functions
# ==================================================================

def utc_now() -> str:
    """
    Return an ISO-8601 UTC timestamp.
    """

    return datetime.now(timezone.utc).isoformat()


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 without loading the entire file into memory.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def discover_images(root_directory: Path) -> list[Path]:
    """
    Find all supported image files recursively.
    """

    if not root_directory.exists():
        raise FileNotFoundError(
            f"Image directory does not exist:\n{root_directory}"
        )

    if not root_directory.is_dir():
        raise NotADirectoryError(
            f"Image path is not a directory:\n{root_directory}"
        )

    images = [
        path
        for path in root_directory.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
    ]

    return sorted(
        images,
        key=lambda path: str(path).lower(),
    )


def load_database(json_path: Path) -> dict[str, Any]:
    """
    Load imageCloud.json or return a new database.
    """

    if not json_path.exists():
        return {
            "version": 1,
            "model": MODEL_NAME,
            "imageRoot": str(IMAGE_ROOT),
            "generatedAt": None,
            "totalImages": 0,
            "images": [],
        }

    try:
        with json_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid JSON in {json_path}:\n{error}"
        ) from error

    if not isinstance(data, dict):
        raise RuntimeError(
            f"{json_path} must contain a JSON object."
        )

    images = data.get("images")

    if not isinstance(images, list):
        data["images"] = []

    return data


def save_database(
    json_path: Path,
    database: dict[str, Any],
) -> None:
    """
    Save JSON safely using a temporary file.
    """

    json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    database["version"] = 1
    database["model"] = MODEL_NAME
    database["imageRoot"] = str(IMAGE_ROOT)
    database["generatedAt"] = utc_now()
    database["totalImages"] = len(
        database.get("images", [])
    )

    temporary_file = json_path.with_suffix(".json.tmp")

    with temporary_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            database,
            file,
            indent=2,
            ensure_ascii=False,
        )

    temporary_file.replace(json_path)


def clean_json_response(response_text: str) -> str:
    """
    Remove optional Markdown JSON fences.
    """

    text = response_text.strip()

    text = text.removeprefix("```json")
    text = text.removeprefix("```")
    text = text.removesuffix("```")

    return text.strip()


def validate_gemini_result(
    result: Any,
) -> dict[str, str]:
    """
    Validate and normalize Gemini metadata.
    """

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini response must be a JSON object."
        )

    required_fields = {
        "title",
        "category",
        "alt",
    }

    missing_fields = required_fields - result.keys()

    if missing_fields:
        raise ValueError(
            "Gemini response is missing: "
            + ", ".join(sorted(missing_fields))
        )

    normalized: dict[str, str] = {}

    for field_name in required_fields:
        value = result.get(field_name)

        if not isinstance(value, str):
            raise ValueError(
                f"Gemini field '{field_name}' must be text."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"Gemini field '{field_name}' cannot be empty."
            )

        normalized[field_name] = value

    return normalized


def get_image_dimensions(
    image_path: Path,
) -> tuple[int | None, int | None]:
    """
    Return image width and height.
    """

    try:
        with Image.open(image_path) as image:
            return image.width, image.height

    except Exception:
        return None, None


def normalize_relative_path(
    image_path: Path,
) -> str:
    """
    Return a web-friendly relative image path.
    """

    return image_path.relative_to(
        IMAGE_ROOT
    ).as_posix()


def create_record_id(
    sha256_hash: str,
    relative_path: str,
) -> str:
    """
    Build a stable ID based primarily on image content.
    """

    path_hash = hashlib.sha256(
        relative_path.encode("utf-8")
    ).hexdigest()[:8]

    return f"{sha256_hash[:16]}-{path_hash}"


# ==================================================================
# Gemini analysis
# ==================================================================

def analyze_image_with_gemini(
    client: genai.Client,
    image_path: Path,
) -> dict[str, str]:
    """
    Send one image to Gemini with retry handling.
    """

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with Image.open(image_path) as source_image:
                image = source_image.convert("RGB")

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=[
                        IMAGE_PROMPT,
                        image,
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            cleaned_text = clean_json_response(
                response.text
            )

            parsed_result = json.loads(cleaned_text)

            return validate_gemini_result(
                parsed_result
            )

        except UnidentifiedImageError:
            raise RuntimeError(
                f"Invalid or unsupported image: {image_path}"
            )

        except Exception as error:
            last_error = error

            if attempt >= MAX_RETRIES:
                break

            waiting_time = (
                RETRY_BASE_SECONDS
                * (2 ** (attempt - 1))
            )

            print(
                f"    Request failed on attempt "
                f"{attempt}/{MAX_RETRIES}."
            )
            print(
                f"    Retrying in {waiting_time} seconds..."
            )
            print(f"    Error: {error}")

            time.sleep(waiting_time)

    raise RuntimeError(
        f"Gemini analysis failed after "
        f"{MAX_RETRIES} attempts: {last_error}"
    )


# ==================================================================
# Existing-record indexes
# ==================================================================

def create_indexes(
    records: list[dict[str, Any]],
) -> tuple[
    dict[str, list[dict[str, Any]]],
    dict[str, dict[str, Any]],
]:
    """
    Build indexes by SHA-256 and relative path.
    """

    by_hash: dict[
        str,
        list[dict[str, Any]]
    ] = {}

    by_path: dict[
        str,
        dict[str, Any]
    ] = {}

    for record in records:
        sha256_hash = record.get("sha256")
        relative_path = record.get("relativePath")

        if isinstance(sha256_hash, str):
            by_hash.setdefault(
                sha256_hash,
                [],
            ).append(record)

        if isinstance(relative_path, str):
            by_path[relative_path] = record

    return by_hash, by_path


def find_missing_original_record(
    records_with_hash: list[dict[str, Any]],
    discovered_relative_paths: set[str],
) -> dict[str, Any] | None:
    """
    Detect a renamed image.

    A record with the same hash whose old path no longer exists is
    considered the original record for the renamed file.
    """

    for record in records_with_hash:
        old_path = record.get("relativePath")

        if (
            isinstance(old_path, str)
            and old_path not in discovered_relative_paths
        ):
            return record

    return None


# ==================================================================
# Main processing
# ==================================================================

def process_images(
    force: bool,
    dry_run: bool,
    limit: int | None,
) -> int:
    """
    Analyze new and changed images.
    """

    load_dotenv(
        ENV_FILE,
        override=True,
    )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print(
            f"ERROR: GEMINI_API_KEY was not found in:\n"
            f"{ENV_FILE}"
        )
        return 1

    images = discover_images(IMAGE_ROOT)

    if limit is not None:
        images = images[:limit]

    database = load_database(OUTPUT_JSON)

    existing_records = database.get("images", [])

    if not isinstance(existing_records, list):
        existing_records = []

    discovered_relative_paths = {
        normalize_relative_path(image_path)
        for image_path in images
    }

    by_hash, by_path = create_indexes(
        existing_records
    )

    client = genai.Client(api_key=api_key)

    processed_count = 0
    skipped_count = 0
    renamed_count = 0
    reused_count = 0
    failed_count = 0

    print("=" * 80)
    print("IMAGE CLOUD — GEMINI ANALYZER")
    print("=" * 80)
    print(f"Image folder : {IMAGE_ROOT}")
    print(f"Output file  : {OUTPUT_JSON}")
    print(f"Model        : {MODEL_NAME}")
    print(f"Images found : {len(images)}")
    print(f"Force        : {force}")
    print(f"Dry run      : {dry_run}")
    print("=" * 80)

    try:
        for index, image_path in enumerate(
            images,
            start=1,
        ):
            relative_path = normalize_relative_path(
                image_path
            )

            print(
                f"\n[{index}/{len(images)}] "
                f"{relative_path}"
            )

            try:
                sha256_hash = calculate_sha256(
                    image_path
                )

                existing_path_record = by_path.get(
                    relative_path
                )

                # --------------------------------------------------
                # Exact path and exact content already processed
                # --------------------------------------------------

                if (
                    not force
                    and existing_path_record
                    and existing_path_record.get("sha256")
                    == sha256_hash
                ):
                    print("    SKIPPED: unchanged image")
                    skipped_count += 1
                    continue

                same_hash_records = by_hash.get(
                    sha256_hash,
                    [],
                )

                # --------------------------------------------------
                # Renamed image
                # --------------------------------------------------

                renamed_record = (
                    find_missing_original_record(
                        same_hash_records,
                        discovered_relative_paths,
                    )
                )

                if (
                    not force
                    and renamed_record is not None
                ):
                    old_path = renamed_record.get(
                        "relativePath"
                    )

                    print(
                        f"    RENAMED: {old_path} "
                        f"-> {relative_path}"
                    )

                    renamed_record["fileName"] = (
                        image_path.name
                    )
                    renamed_record["relativePath"] = (
                        relative_path
                    )
                    renamed_record["extension"] = (
                        image_path.suffix.lower()
                    )
                    renamed_record["updatedAt"] = utc_now()

                    width, height = get_image_dimensions(
                        image_path
                    )

                    renamed_record["width"] = width
                    renamed_record["height"] = height
                    renamed_record["sizeBytes"] = (
                        image_path.stat().st_size
                    )

                    if not dry_run:
                        save_database(
                            OUTPUT_JSON,
                            database,
                        )

                    renamed_count += 1

                    by_path.pop(
                        str(old_path),
                        None,
                    )
                    by_path[relative_path] = (
                        renamed_record
                    )

                    continue

                # --------------------------------------------------
                # Duplicate file content at another active path
                # Reuse analysis without another Gemini request.
                # --------------------------------------------------

                if (
                    not force
                    and same_hash_records
                ):
                    source_record = same_hash_records[0]

                    print(
                        "    REUSED: identical content was "
                        "already analyzed"
                    )

                    width, height = get_image_dimensions(
                        image_path
                    )

                    new_record = deepcopy(source_record)

                    new_record["id"] = create_record_id(
                        sha256_hash,
                        relative_path,
                    )
                    new_record["fileName"] = image_path.name
                    new_record["relativePath"] = relative_path
                    new_record["extension"] = (
                        image_path.suffix.lower()
                    )
                    new_record["mimeType"] = (
                        mimetypes.guess_type(
                            image_path.name
                        )[0]
                        or "application/octet-stream"
                    )
                    new_record["sizeBytes"] = (
                        image_path.stat().st_size
                    )
                    new_record["width"] = width
                    new_record["height"] = height
                    new_record["createdAt"] = utc_now()
                    new_record["updatedAt"] = utc_now()
                    new_record["analysisReused"] = True

                    if existing_path_record:
                        existing_records.remove(
                            existing_path_record
                        )

                    existing_records.append(new_record)

                    by_path[relative_path] = new_record
                    by_hash.setdefault(
                        sha256_hash,
                        [],
                    ).append(new_record)

                    if not dry_run:
                        save_database(
                            OUTPUT_JSON,
                            database,
                        )

                    reused_count += 1
                    continue

                # --------------------------------------------------
                # New or modified file
                # --------------------------------------------------

                if dry_run:
                    if existing_path_record:
                        print(
                            "    WOULD ANALYZE: file content changed"
                        )
                    else:
                        print(
                            "    WOULD ANALYZE: new image"
                        )

                    continue

                if existing_path_record:
                    print(
                        "    ANALYZING: image content changed"
                    )
                else:
                    print("    ANALYZING: new image")

                gemini_result = analyze_image_with_gemini(
                    client,
                    image_path,
                )

                width, height = get_image_dimensions(
                    image_path
                )

                now = utc_now()

                record = {
                    "id": create_record_id(
                        sha256_hash,
                        relative_path,
                    ),
                    "fileName": image_path.name,
                    "relativePath": relative_path,
                    "extension": image_path.suffix.lower(),
                    "mimeType": (
                        mimetypes.guess_type(
                            image_path.name
                        )[0]
                        or "application/octet-stream"
                    ),
                    "sizeBytes": image_path.stat().st_size,
                    "width": width,
                    "height": height,
                    "sha256": sha256_hash,
                    "title": gemini_result["title"],
                    "category": gemini_result["category"],
                    "alt": gemini_result["alt"],
                    "model": MODEL_NAME,
                    "analysisReused": False,
                    "createdAt": (
                        existing_path_record.get("createdAt")
                        if existing_path_record
                        else now
                    ),
                    "updatedAt": now,
                }

                if existing_path_record:
                    record_index = existing_records.index(
                        existing_path_record
                    )

                    old_hash = existing_path_record.get(
                        "sha256"
                    )

                    existing_records[record_index] = record

                    if isinstance(old_hash, str):
                        old_hash_records = by_hash.get(
                            old_hash,
                            [],
                        )

                        if existing_path_record in old_hash_records:
                            old_hash_records.remove(
                                existing_path_record
                            )

                else:
                    existing_records.append(record)

                by_path[relative_path] = record

                by_hash.setdefault(
                    sha256_hash,
                    [],
                ).append(record)

                database["images"] = existing_records

                save_database(
                    OUTPUT_JSON,
                    database,
                )

                processed_count += 1

                print(
                    f"    SAVED: {gemini_result['title']}"
                )
                print(
                    f"    CATEGORY: "
                    f"{gemini_result['category']}"
                )

            except Exception as error:
                failed_count += 1

                print("    FAILED")
                print(
                    f"    {type(error).__name__}: {error}"
                )

                traceback.print_exc()

        database["images"] = existing_records

        if not dry_run:
            save_database(
                OUTPUT_JSON,
                database,
            )

    finally:
        client.close()

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"New/updated analyzed : {processed_count}")
    print(f"Unchanged skipped    : {skipped_count}")
    print(f"Renamed detected     : {renamed_count}")
    print(f"Duplicate reused     : {reused_count}")
    print(f"Failed               : {failed_count}")
    print(f"JSON records         : {len(existing_records)}")
    print(f"Output               : {OUTPUT_JSON}")
    print("=" * 80)

    return 0 if failed_count == 0 else 2


# ==================================================================
# Command-line arguments
# ==================================================================

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze images with Gemini and skip unchanged "
            "images using SHA-256."
        )
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Analyze every image again, even when its hash "
            "already exists."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Show which images would be analyzed without "
            "calling Gemini or changing JSON."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Process only the first N discovered images."
        ),
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    if (
        arguments.limit is not None
        and arguments.limit < 1
    ):
        print("--limit must be greater than zero.")
        sys.exit(1)

    exit_code = process_images(
        force=arguments.force,
        dry_run=arguments.dry_run,
        limit=arguments.limit,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()