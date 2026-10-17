import logging
import os
import pathlib
import random
import shutil
import string
import time
import uuid

import constants as c
import resources.Environment as Env
from src.utils.image_fetch import fetch_to_file


def download_temp_file(
    url: str, extension: str = None, expect_image: bool = False, timeout: float = 30
) -> str:
    """
    Download file to temp folder, the way a browser would (see image_fetch.py: when the host
    doesn't take the request of a script, the other ways to download it are tried before giving up)
    :param url: url of file
    :param extension: File extension
    :param expect_image: If the file has to be an image. A host that blocks the bot often answers
    with a web page instead of an error, which is then not taken as a file that was downloaded
    :param timeout: Seconds to wait for the host in every request
    :return: path of downloaded file
    :raises urllib.error.HTTPError, urllib.error.URLError: If the file can't be downloaded in any way
    """

    # Create temp folder
    if not os.path.exists(c.TEMP_DIR):
        os.makedirs(c.TEMP_DIR)

    # File name
    extension = pathlib.Path(url).suffix if extension is None else extension
    file_path = generate_temp_file_path(extension)

    fetch_to_file(url, file_path, timeout=timeout, expect_image=expect_image)

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
