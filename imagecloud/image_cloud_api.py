import json
import math
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse


router = APIRouter(
    prefix="/api/image-cloud",
    tags=["Image Cloud"],
)


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

#BACKEND_ROOT = Path(r"D:\react-app-oct\txta")

#IMAGE_ROOT = BACKEND_ROOT / "brahma"
# image_cloud_api.py is inside:
# txta/imagecloud/image_cloud_api.py

IMAGECLOUD_MODULE_FOLDER = Path(__file__).resolve().parent

# Go one level up:
# txta/
BACKEND_ROOT = IMAGECLOUD_MODULE_FOLDER.parent

BRAHMA_FOLDER = BACKEND_ROOT / "brahma"




IMAGECLOUD_JSON = (
    IMAGECLOUD_MODULE_FOLDER
    / "output"
    / "imageCloud.json"
)

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


print(f"[Image Cloud] Module folder: {IMAGECLOUD_MODULE_FOLDER}")
print(f"[Image Cloud] Backend root: {BACKEND_ROOT}")
print(f"[Image Cloud] Brahma folder: {BRAHMA_FOLDER}")
print(f"[Image Cloud] JSON file: {IMAGECLOUD_JSON}")
print(f"[Image Cloud] JSON exists: {IMAGECLOUD_JSON.is_file()}")
# ---------------------------------------------------------
# JSON loading
# ---------------------------------------------------------

def load_image_cloud_database() -> dict[str, Any]:
    if not IMAGECLOUD_JSON.is_file():
        raise HTTPException(
            status_code=503,
            detail=(
                "Image Cloud data is unavailable. "
                "Run analyze_images.py first."
            ),
        )

    try:
        with IMAGECLOUD_JSON.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid imageCloud.json: {error}",
        ) from error

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=500,
            detail="imageCloud.json must contain an object.",
        )

    images = data.get("images")

    if not isinstance(images, list):
        raise HTTPException(
            status_code=500,
            detail="imageCloud.json has no valid images array.",
        )

    return data


# ---------------------------------------------------------
# Record normalization
# ---------------------------------------------------------

def create_image_url(
    relative_path: str,
    base_url: str,
) -> str:
    clean_path = relative_path.replace("\\", "/").lstrip("/")

    return f"{base_url.rstrip('/')}/imagecloud/{clean_path}"


def normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    return value.strip()


def normalize_record(
    record: dict[str, Any],
    base_url: str,
) -> dict[str, Any]:
    relative_path = normalize_text(
        record.get("relativePath")
    )

    return {
        "id": normalize_text(record.get("id")),
        "fileName": normalize_text(
            record.get("fileName")
        ),
        "relativePath": relative_path,
        "src": create_image_url(
            relative_path,
            base_url,
        ),
        "title": normalize_text(
            record.get("title")
        ),
        "category": normalize_text(
            record.get("category")
        ),
        "alt": normalize_text(
            record.get("alt")
        ),
        "width": record.get("width"),
        "height": record.get("height"),
        "sizeBytes": record.get("sizeBytes"),
        "mimeType": record.get("mimeType"),
        "sha256": record.get("sha256"),
        "createdAt": record.get("createdAt"),
        "updatedAt": record.get("updatedAt"),
    }


# ---------------------------------------------------------
# Filtering
# ---------------------------------------------------------

def matches_category(
    image: dict[str, Any],
    category: str,
) -> bool:
    if not category or category.casefold() == "all":
        return True

    image_category = normalize_text(
        image.get("category")
    )

    return (
        image_category.casefold()
        == category.casefold()
    )


def matches_search(
    image: dict[str, Any],
    search: str,
) -> bool:
    normalized_search = search.strip().casefold()

    if not normalized_search:
        return True

    searchable_text = " ".join(
        [
            normalize_text(image.get("title")),
            normalize_text(image.get("category")),
            normalize_text(image.get("alt")),
            normalize_text(image.get("fileName")),
        ]
    ).casefold()

    return normalized_search in searchable_text


# ---------------------------------------------------------
# API endpoint
# ---------------------------------------------------------

@router.get("")
def get_image_cloud(
    category: str = Query(
        default="All",
        max_length=100,
    ),
    search: str = Query(
        default="",
        max_length=200,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=24,
        ge=1,
        le=MAX_PAGE_SIZE,
        alias="pageSize",
    ),
) -> JSONResponse:
    database = load_image_cloud_database()

    source_images = database.get("images", [])

    # Render production URL
    base_url = "https://txta-1.onrender.com"

    images = [
        normalize_record(record, base_url)
        for record in source_images
        if isinstance(record, dict)
    ]

    filtered_images = [
        image
        for image in images
        if (
            matches_category(image, category)
            and matches_search(image, search)
        )
    ]

    filtered_images.sort(
        key=lambda image: (
            image.get("updatedAt") or "",
            image.get("title") or "",
        ),
        reverse=True,
    )

    total_items = len(filtered_images)

    total_pages = max(
        1,
        math.ceil(total_items / page_size),
    )

    safe_page = min(page, total_pages)

    start_index = (
        safe_page - 1
    ) * page_size

    end_index = start_index + page_size

    page_images = filtered_images[
        start_index:end_index
    ]

    categories = sorted(
        {
            normalize_text(image.get("category"))
            for image in images
            if normalize_text(image.get("category"))
        },
        key=str.casefold,
    )

    response = {
        "metadata": {
            "generatedAt": database.get(
                "generatedAt"
            ),
            "model": database.get("model"),
            "totalAvailableImages": len(images),
        },
        "filters": {
            "category": category,
            "search": search,
        },
        "pagination": {
            "page": safe_page,
            "pageSize": page_size,
            "totalItems": total_items,
            "totalPages": total_pages,
            "hasPreviousPage": safe_page > 1,
            "hasNextPage": safe_page < total_pages,
        },
        "categories": [
            "All",
            *categories,
        ],
        "images": page_images,
    }

    return JSONResponse(
        content=response,
        headers={
            "Cache-Control": (
                "public, max-age=60, s-maxage=300"
            ),
        },
    )