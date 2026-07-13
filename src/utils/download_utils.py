import logging
import os
import pathlib
import random
import shutil
import string
import time
import urllib.error
import urllib.request
import uuid

import constants as c
import resources.Environment as Env


def download_temp_file(url: str, extension: str = None) -> str:
    """
    Download file to temp folder
    :param url: url of file
    :param extension: File extension
    :return: path of downloaded file
    """

    # Create temp folder
    if not os.path.exists(c.TEMP_DIR):
        os.makedirs(c.TEMP_DIR)

    # File name
    extension = pathlib.Path(url).suffix if extension is None else extension
    file_path = generate_temp_file_path(extension)

    # Download file with a browser-like User-Agent to avoid blocking by some hosts
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                with open(file_path, "wb") as out_file:
                    shutil.copyfileobj(response, out_file)
            return file_path
        except urllib.error.HTTPError as e:
            # Retry transient server-side or rate limit errors once
            if attempt < 2 and e.code in {429, 502, 503, 504}:
                time.sleep(1)
                continue
            raise
        except urllib.error.URLError:
            if attempt < 2:
                time.sleep(1)
                continue
            raise

    return file_path


def cleanup_temp_dir() -> None:
    """
    Removes files older than x time from temp folder
    """

    current_time = time.time()
    time_limit = float(Env.TEMP_DIR_CLEANUP_TIME_SECONDS.get())

    # Delete temp folder
    if os.path.exists(c.TEMP_DIR):  # Temp folder exists
        for file in os.listdir(c.TEMP_DIR):  # Iterate files in folder
            file_path = os.path.join(c.TEMP_DIR, file)
            try:
                pathinfo = os.stat(file_path)
                if (
                    pathinfo.st_ctime < current_time - time_limit or True
                ):  # File is older than x time
                    if os.path.isfile(file_path):  # Is a file
                        os.unlink(file_path)
                    else:
                        shutil.rmtree(file_path)  # Is a folder
            except Exception as e:
                logging.error("Error while deleting temp path: %s", e)


def generate_temp_file_path(extension: str) -> str:
    """
    Generate temp file path
    :param extension: file extension
    :type extension: str
    :return: path of temp file
    """

    # Ensure temp directory exists before generating paths used by file writers.
    os.makedirs(c.TEMP_DIR, exist_ok=True)

    # File name
    file_name = uuid.uuid4().hex + ("." if not extension.startswith(".") else "") + extension

    # File path
    return os.path.join(c.TEMP_DIR, file_name)


def get_random_string(length: int = 10) -> str:
    """
    Create a random string
    :param length: The length of the string
    :return: The random string
    """

    # Define the characters you want to include in the random string
    characters = (
        string.ascii_letters + string.digits
    )  # includes uppercase letters, lowercase letters, and digits

    # Generate a random string of length 10
    return "".join(random.choice(characters) for _ in range(length))
