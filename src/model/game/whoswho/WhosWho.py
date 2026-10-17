import logging
import os
import shutil
import urllib.error
from PIL import Image, ImageFilter

import constants as c
from src.model.game.GameBoard import GameBoard
from src.model.wiki.Character import Character
from src.utils.download_utils import generate_temp_file_path, download_temp_file
from src.utils.image_fetch import get_bundled_image_file_name

# Images of the characters that come with the bot, so that the game doesn't depend on the host of
# the images accepting the downloads of this server (see scripts/download_character_images.py)
BUNDLED_IMAGES_DIR = os.path.join(c.ASSETS_IMAGES_DIR, "characters")

# How long to wait for the host of the images in every request. The bot is blocked while it waits
IMAGE_DOWNLOAD_TIMEOUT_SECONDS = 15

# Images bigger than this (in pixels) are refused: they'd take too much memory to be blurred
MAX_IMAGE_PIXELS = 40_000_000


class WhosWho(GameBoard):
    def __init__(
        self,
        character: Character,
        image_path: str = None,
        level: int = 5,
        latest_blurred_image: str = None,
        revealed_letters_count: int = 0,
    ):
        """
        Constructor
        :param character: The character
        :param image_path: The downloaded image path
        :param level: The level
        :param latest_blurred_image: The latest blurred image tg media id
        :param revealed_letters_count: The revealed letters count
        """
        super().__init__()

        self.character = character
        self.image_path = image_path
        self.level = level
        self.latest_blurred_image = latest_blurred_image
        self.revealed_letters_count = revealed_letters_count

        # Re-download the image if it doesn't exist because it was deleted
        if self.image_path is not None:
            try:
                with Image.open(self.image_path):
                    pass
            except FileNotFoundError:
                self._safe_download_image()
        else:
            self._safe_download_image()

        # Reset the blurred image if it doesn't exist because it was deleted
        if self.latest_blurred_image is not None:
            try:
                with Image.open(self.latest_blurred_image):
                    pass
            except FileNotFoundError:
                self.set_blurred_image()

        if self.latest_blurred_image is None:
            self.set_blurred_image()

    def _safe_download_image(self):
        """
        Safely gets the character image: the one that comes bundled with the bot if there is one,
        else by downloading it.
        Raises ValueError if it can't be got (e.g., 404 Not Found)
        """

        if self._use_bundled_image():
            return

        if not self.character.anime_image_url:
            logging.warning(f"Character {self.character.name} has no image url")
            raise ValueError(f"Image unavailable for {self.character.name} (no image url)")

        try:
            image_path = download_temp_file(
                self.character.anime_image_url,
                "jpg",
                expect_image=True,
                timeout=IMAGE_DOWNLOAD_TIMEOUT_SECONDS,
            )
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logging.warning(f"Dead image link for {self.character.name}: {e}")
            raise ValueError(f"Image unavailable for {self.character.name} ({e})")
        except Exception as e:
            logging.warning(f"Failed to process image for {self.character.name}: {e}")
            raise ValueError(f"Image processing failed for {self.character.name} ({e})")

        try:
            self._prepare_image(image_path)
        except Exception as e:
            self._remove_file(image_path)
            logging.warning(f"Failed to process image for {self.character.name}: {e}")
            raise ValueError(f"Image processing failed for {self.character.name} ({e})")

        self.image_path = image_path

    def _use_bundled_image(self) -> bool:
        """
        Use the image of the character that comes bundled with the bot, if it has one and it works
        :return: True if the image was set, False if it has to be downloaded
        """

        if not self.character.anime_image_url:
            return False

        bundled_path = os.path.join(
            BUNDLED_IMAGES_DIR, get_bundled_image_file_name(self.character.anime_image_url)
        )
        if not os.path.isfile(bundled_path):
            return False

        # A copy, as if it had been downloaded: the game can do whatever it wants with its image
        image_path = generate_temp_file_path("jpg")
        try:
            shutil.copyfile(bundled_path, image_path)
            self._prepare_image(image_path)
        except Exception as e:
            # E.g. a Git LFS pointer, or an empty file, deployed instead of the image
            self._remove_file(image_path)
            logging.warning(
                f"The bundled image of {self.character.name} ({bundled_path}) can't be used, "
                f"downloading it instead: {e}"
            )
            return False

        self.image_path = image_path
        return True

    @staticmethod
    def _prepare_image(path: str) -> None:
        """
        Check that an image file can be used by the game: that it is an image, complete, and not too
        big. Anything other than a JPEG or a PNG is also converted to a JPEG, since Telegram doesn't
        take every format as a photo (a WebP, for example)
        :param path: The path of the image
        :return: None
        :raises Exception: If the file can't be used
        """

        with Image.open(path) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError(f"The image is too big ({image.width}x{image.height})")

            image.load()

            if image.format in ("JPEG", "PNG"):
                return

            converted_image = image.convert("RGB")

        converted_image.save(path, format="JPEG", quality=92)

    @staticmethod
    def _remove_file(path: str) -> None:
        """
        Remove a file, if it is there
        :param path: The path of the file
        :return: None
        """

        try:
            os.remove(path)
        except OSError:
            pass

    def set_blurred_image(self):
        """
        Set the blurred image
        :return: None
        """

        with Image.open(self.image_path) as image:
            image = image.convert("RGB")
            image = image.filter(ImageFilter.GaussianBlur((self.level - 1) * 10))
            save_path = generate_temp_file_path("jpg")
            image.save(save_path)
            self.latest_blurred_image = save_path

    def reduce_level(self):
        """
        Reduce the level
        :return: None
        """
        if self.level > 0:
            self.level -= 1
            self.set_blurred_image()

    def can_reduce_level(self) -> bool:
        """
        Check if the level can be reduced
        :return: bool
        """
        return self.level > 1

    def is_correct(self, answer: str) -> bool:
        """
        Check if the answer is correct
        :param answer: The answer
        :return: bool
        """
        return answer is not None and answer.lower() == self.character.name.lower()

    def have_revealed_all_letters(self) -> bool:
        """
        Check if all letters have been revealed
        :return: bool
        """
        return self.revealed_letters_count == len(self.character.name)
