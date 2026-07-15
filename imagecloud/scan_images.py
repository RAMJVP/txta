import os

from helpers import calculate_sha256
from helpers import SUPPORTED_EXTENSIONS


IMAGE_FOLDER = r"D:\react-app-oct\txta\brahma"
#IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), "txta", "brahma")


def scan():

    images = []

    for root, dirs, files in os.walk(IMAGE_FOLDER):

        for file in files:

            if file.lower().endswith(SUPPORTED_EXTENSIONS):

                full_path = os.path.join(root, file)

                sha = calculate_sha256(full_path)

                images.append({

                    "fileName": file,

                    "fullPath": full_path,

                    "sha256": sha

                })

    return images


if __name__ == "__main__":

    image_list = scan()

    print("=" * 80)

    print(f"Total Images : {len(image_list)}")

    print("=" * 80)

    for image in image_list:

        print()

        print(image["fileName"])

        print(image["sha256"])

        print(image["fullPath"])