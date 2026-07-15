import hashlib
import json
import os
import re
from pathlib import Path


SUPPORTED_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif"
)


def calculate_sha256(file_path):
    """
    Calculate SHA256 hash of an image.
    """

    sha = hashlib.sha256()

    with open(file_path, "rb") as f:

        while True:

            chunk = f.read(8192)

            if not chunk:
                break

            sha.update(chunk)

    return sha.hexdigest()


def slugify(text):
    """
    Convert title into SEO friendly slug.

    Example:

    Miracle Red Juice

    becomes

    miracle-red-juice
    """

    text = text.lower().strip()

    text = re.sub(r'[^a-z0-9\s-]', '', text)

    text = re.sub(r'\s+', '-', text)

    text = re.sub(r'-+', '-', text)

    return text


def load_json(json_file):

    if not os.path.exists(json_file):
        return []

    with open(json_file, "r", encoding="utf-8") as f:

        return json.load(f)


def save_json(json_file, data):

    Path(json_file).parent.mkdir(parents=True, exist_ok=True)

    with open(json_file, "w", encoding="utf-8") as f:

        json.dump(data, f, indent=4, ensure_ascii=False)