import asyncio
import logging
import os
import re
import unicodedata

from confusable_homoglyphs import confusables
from PIL import Image, ImageDraw, ImageFont
from PIL import features as pil_features
from src.tg_compat import Update
from unidecode import unidecode
from wantedposter.wantedposter import (
    WantedPoster,
    VerticalAlignment,
    CaptureCondition,
    Effect,
    Stamp,
    BOUNTY_POSTER_NAME_TEXTURE_PATH,
    BOUNTY_POSTER_NAME_FONT_SIZE,
    BOUNTY_POSTER_NAME_MAX_W,
    BOUNTY_POSTER_NAME_H,
    BOUNTY_POSTER_NAME_START_Y,
)

import constants as c
from src.model.Leaderboard import Leaderboard
from src.model.LeaderboardUser import LeaderboardUser
from src.model.User import User
from src.model.enums.BossType import BossType
from src.model.enums.LeaderboardRank import LeaderboardRank, get_rank_by_index
from src.service.devil_fruit_service import user_has_eaten_devil_fruit
from src.utils.download_utils import generate_temp_file_path

# Native-script rendering (see NATIVE_SCRIPT_FONT_MAP below) needs Pillow's raqm text layout
# engine for correct shaping/direction (e.g. Arabic letter joining). Not every environment's
# Pillow build/system libraries have it available -- when it's missing, Pillow doesn't fail
# gracefully, it raises a hard error the moment a direction/shaping argument is used. Checked
# once here so native-script rendering can be skipped safely (falling back to the existing
# transliteration pipeline) on environments where it's not supported, instead of crashing
RAQM_AVAILABLE = pil_features.check("raqm")

# Fallback name used in the extremely rare case where, after sanitization, nothing
# usable is left of a player's name (e.g. it was made up entirely of emoji/symbols)
BOUNTY_POSTER_FALLBACK_NAME = "Unknown"

# Scripts a player's name can be shown in as-is, instead of being transliterated to English.
# Each entry maps the Unicode script name (the prefix of unicodedata.name() for a character in
# that script, e.g. "ARABIC LETTER SEEN" -> "ARABIC") to a font file that supports it and its
# writing direction. The poster's own font (Playfair Display) only covers Latin, so showing any
# of these scripts as-is means bypassing the poster library's name rendering for a custom one
# (see _build_mixed_script_name_component). Not exhaustive -- add an entry here (and the
# matching font file under assets/fonts) to support more scripts
NATIVE_SCRIPT_FONT_MAP = {
    "ARABIC": (os.path.join(c.ASSETS_FONTS_DIR, "NotoSansArabic-Bold.ttf"), "rtl"),
    "DEVANAGARI": (os.path.join(c.ASSETS_FONTS_DIR, "NotoSansDevanagari-Bold.ttf"), "ltr"),
}

# Used for the Latin/neutral portions of a name that also contains native-script text (see
# _build_mixed_script_name_component), so that e.g. "apple سیب FARZIN" shows "apple"/"FARZIN" as
# actual Latin glyphs instead of unsupported-glyph placeholder boxes (NotoSansArabic/Devanagari
# don't cover Latin). Matches the poster library's own name font
LATIN_NAME_FONT_PATH = os.path.join(c.ASSETS_FONTS_DIR, "Blogger_Sans-Bold.otf")


# "Fancy font" generators (common for Discord/Telegram display names) often reuse characters
# from completely unrelated scripts purely because they look like Latin letters (e.g. Canadian
# Aboriginal Syllabics, Cherokee). unidecode has no way to know this -- it transliterates based
# on the character's real phonetic meaning, not its visual shape, so these end up turning into
# unrelated syllables (e.g. "ᖇ" looks like "R" but unidecode reads it as the Cree syllable
# "tlhi", "Ꮿ" looks like "W" but unidecode reads it as the Cherokee syllable "ya"). This map
# catches reported cases by mapping the visual look-alike directly to the Latin letter it's
# actually being used to represent, bypassing unidecode for these characters. Not exhaustive --
# there are many different "fancy font" styles in the wild -- but can be extended here whenever
# a new one is reported
FANCY_FONT_LOOKALIKE_CHAR_MAP = {
    "ᖇ": "R",  # Canadian Syllabics Tlhi, used to look like "R"
    "ᑢ": "C",  # Canadian Syllabics West-Cree Twa, used to look like "C"
    "ᒪ": "L",  # Canadian Syllabics Ma, used to look like "L"
    "ᘿ": "E",  # Canadian Syllabics Carrier Tla, used to look like "E"
    "Ꮋ": "H",  # Cherokee Letter Mi, used to look like "H"
    "Ꮿ": "W",  # Cherokee Letter Ya, used to look like "W"
    "Ꮇ": "M",  # Cherokee Letter Lu, used to look like "M"
}


def get_native_script(name: str) -> str | None:
    """
    Detects whether a name is written in a script we can show as-is on the poster (see
    NATIVE_SCRIPT_FONT_MAP), by checking each character's Unicode name (e.g. a character named
    "ARABIC LETTER SEEN" belongs to the "ARABIC" script)
    :param name: The raw name, as it is on Telegram
    :return: The script name (a key of NATIVE_SCRIPT_FONT_MAP) if found, otherwise None
    """

    for char in name:
        if char.isspace() or not char.isalpha():
            continue

        try:
            char_name = unicodedata.name(char)
        except ValueError:
            continue

        for script in NATIVE_SCRIPT_FONT_MAP:
            if char_name.startswith(script):
                return script

    return None


def _segment_by_script(text: str) -> list[tuple[str, str | None]]:
    """
    Segments text into contiguous runs of a single native script (see NATIVE_SCRIPT_FONT_MAP) or
    plain Latin/neutral characters (Latin letters, digits, punctuation, spaces), so a name that
    mixes scripts (e.g. "apple سیب FARZIN") can have each part rendered with a font that actually
    supports it, instead of forcing the whole string through a single script's font.
    :param text: The text to segment
    :return: A list of (segment_text, script) tuples in original order. script is a key of
    NATIVE_SCRIPT_FONT_MAP for a native-script run, or None for a Latin/neutral run
    """

    runs: list[tuple[str, str | None]] = []
    current_text = ""
    current_script: str | None = None

    for char in text:
        char_script = None

        if unicodedata.category(char).startswith("M"):
            # Combining mark (e.g. a Devanagari vowel sign) - not alphabetic on its own, but
            # belongs with whatever script precedes it, not a separate "neutral" character.
            # Otherwise it would be wrongly split into its own run and rendered with the Latin
            # font (which doesn't have it), breaking the conjunct/shaping and showing a
            # placeholder box instead
            char_script = current_script
        elif char.isalpha():
            try:
                char_name = unicodedata.name(char)
            except ValueError:
                char_name = ""

            for script in NATIVE_SCRIPT_FONT_MAP:
                if char_name.startswith(script):
                    char_script = script
                    break

        if char_script == current_script:
            current_text += char
        else:
            if current_text:
                runs.append((current_text, current_script))
            current_text = char
            current_script = char_script

    if current_text:
        runs.append((current_text, current_script))

    return runs


def _build_mixed_script_name_component(text: str) -> Image.Image:
    """
    Builds the name texture component for a name that mixes native-script text (see
    NATIVE_SCRIPT_FONT_MAP) with Latin/neutral text (e.g. "apple سیب FARZIN"), rendering each
    part with a font that actually supports it, positioned side by side in their original
    order. Without this, the whole string would be forced through a single native-script font
    (e.g. NotoSansArabic), which doesn't cover Latin characters -- those would show up as
    unsupported-glyph placeholder boxes instead of actual letters.

    Uses a texture + alpha mask, auto-scaling if the combined text is too wide, but draws each
    script run with its own font/direction instead of a single one for the whole string.
    :param text: The full name text, in its original (possibly mixed) script
    :return: The name component image, ready to paste over the poster at
    (0, BOUNTY_POSTER_NAME_START_Y)
    """

    runs = _segment_by_script(text)

    fonts_and_directions: dict[str | None, tuple[ImageFont.FreeTypeFont, str]] = {}
    for _, script in runs:
        if script in fonts_and_directions:
            continue

        if script is None:
            fonts_and_directions[script] = (
                ImageFont.truetype(LATIN_NAME_FONT_PATH, BOUNTY_POSTER_NAME_FONT_SIZE),
                "ltr",
            )
        else:
            font_path, direction = NATIVE_SCRIPT_FONT_MAP[script]
            fonts_and_directions[script] = (
                ImageFont.truetype(
                    font_path, BOUNTY_POSTER_NAME_FONT_SIZE, layout_engine=ImageFont.Layout.RAQM
                ),
                direction,
            )

    texture_background = Image.open(BOUNTY_POSTER_NAME_TEXTURE_PATH)
    texture_background_w, texture_background_h = texture_background.size

    # Measure every run first (on a throwaway draw context) so the combined line can be
    # centered/scaled as a single block, same as the single-script version
    measuring_alpha = Image.new("L", (texture_background_w, texture_background_h))
    measuring_draw = ImageDraw.Draw(measuring_alpha)
    run_widths = [
        measuring_draw.textlength(
            run_text,
            font=fonts_and_directions[script][0],
            direction=fonts_and_directions[script][1],
        )
        for run_text, script in runs
    ]
    total_w = sum(run_widths)

    should_scale = False
    if total_w > BOUNTY_POSTER_NAME_MAX_W:
        new_w = int((total_w * texture_background_w) / BOUNTY_POSTER_NAME_MAX_W)
        alpha = Image.new("L", (new_w, texture_background_h))
        should_scale = True
    else:
        alpha = Image.new("L", (texture_background_w, texture_background_h))

    draw = ImageDraw.Draw(alpha)

    current_x = (alpha.size[0] - total_w) / 2
    for (run_text, script), run_w in zip(runs, run_widths):
        font, direction = fonts_and_directions[script]
        draw.text(
            (current_x + run_w / 2, BOUNTY_POSTER_NAME_H),
            run_text,
            font=font,
            fill="white",
            anchor="ms",
            direction=direction,
        )
        current_x += run_w

    if should_scale:
        alpha = alpha.resize((texture_background_w, texture_background_h))

    texture_background.putalpha(alpha)
    return texture_background


def _get_homoglyph_latin_letter(char: str) -> str | None:
    """
    General-purpose fallback for FANCY_FONT_LOOKALIKE_CHAR_MAP, for "fancy font" look-alike
    characters that haven't been reported/added there yet. Looks up Unicode's own official
    "confusables" data (the same dataset used for anti-phishing/anti-spoofing detection, listing
    characters from any script that are visually confusable with one another) for a plain ASCII
    letter/digit that this character could be mistaken for. Only called for non-ASCII characters,
    since otherwise this would find characters that look like an existing ASCII letter and
    "correct" the letter into a different one (e.g. it considers "l" a look-alike of "1", which
    would wrongly replace a legitimate "1" with "l")
    :param char: A single non-ASCII character
    :return: A single ASCII letter/digit if a confident look-alike is found, otherwise None
    """

    matches = confusables.is_confusable(char, greedy=True)
    if not matches:
        return None

    for match in matches:
        for homoglyph in match.get("homoglyphs", []):
            candidate = homoglyph.get("c", "")
            if len(candidate) == 1 and candidate.isascii() and candidate.isalnum():
                return candidate

    return None


def get_bounty_poster_name(name: str) -> str:
    """
    Sanitizes a name for use on a wanted poster, for scripts that aren't shown as-is (see
    NATIVE_SCRIPT_FONT_MAP / get_native_script).

    The poster font only supports latin characters, so names are normally transliterated
    with unidecode. The problem is that unidecode doesn't just transliterate, it also
    *describes* characters it has no real letter equivalent for (e.g. the chess piece "♚"
    becomes the phrase "black king", an emoji becomes a description, etc.). Those
    descriptions would otherwise be added to the name, making it longer than it should be
    and, in the worst case, pushing it past the point where it gets discarded entirely,
    resulting in a blank name on the poster.

    To support as many characters as possible while avoiding that, every character is
    transliterated individually and only kept if the result is a clean word with no
    spaces in it (e.g. "Ⓐ" -> "A", "Ω" -> "O", "你" -> "Ni", "Ⅷ" -> "VIII" are all kept).
    Characters whose transliteration is a description made up of multiple words (e.g.
    "♚" -> "black king") or that have no latin equivalent at all (most emoji) are
    discarded instead of being spelled out.

    Known "fancy font" look-alike characters (see FANCY_FONT_LOOKALIKE_CHAR_MAP) are mapped
    to their intended Latin letter directly, bypassing unidecode, since unidecode would
    otherwise transliterate them based on their unrelated real meaning instead of their
    intended visual appearance. Any other non-ASCII look-alike not in that map is checked
    against Unicode's official confusables data (see _get_homoglyph_latin_letter) as a general
    safety net, before finally falling back to unidecode
    :param name: The raw name to sanitize, as it is on Telegram
    :return: The sanitized name, safe to pass to the poster generator
    """

    if not name:
        return ""

    kept_chars: list[str] = []
    for char in name:
        if char.isspace():
            kept_chars.append(" ")
            continue

        if char in FANCY_FONT_LOOKALIKE_CHAR_MAP:
            kept_chars.append(FANCY_FONT_LOOKALIKE_CHAR_MAP[char])
            continue

        transliterated = unidecode(char).strip()

        # If unidecode's transliteration is already a single clean letter/digit, trust it --
        # this is the common, correct case (accented letters, fullwidth forms, fancy
        # math/circled Latin letters, etc.). Checking confusables here too could backfire: e.g.
        # it lists "l" as a look-alike of fullwidth "I", which would wrongly override an
        # already-correct "I"
        if len(transliterated) == 1 and transliterated.isalnum():
            kept_chars.append(transliterated)
            continue

        # Otherwise the transliteration is either empty or multiple characters -- suspicious
        # for what's supposed to be a single visual character, and the telltale sign of a
        # "fancy font" character (e.g. Cherokee/Canadian Syllabics look-alikes) being read by
        # its real, unrelated phonetic meaning instead of its intended visual appearance. Check
        # Unicode's confusables data for a better single-letter look-alike before falling back
        if not char.isascii():
            homoglyph = _get_homoglyph_latin_letter(char)
            if homoglyph is not None:
                kept_chars.append(homoglyph)
                continue

        # Keep it only if it's a clean, single alphanumeric "word" - discard descriptive
        # multi-word transliterations as well as the bracket/punctuation placeholder-style
        # output unidecode produces for many decorative/exotic characters it has no real
        # letter equivalent for (e.g. "/XX/" for "༒", "(tm)" for "™", "[(" for "【"). Checking
        # only for the absence of spaces isn't enough - none of those examples contain a space,
        # but none of them are an actual transliteration either
        if transliterated and transliterated.isalnum():
            kept_chars.append(transliterated)

    cleaned = re.sub(r"\s+", " ", "".join(kept_chars)).strip()

    # Strip leftover decorative punctuation often used to bracket/decorate fancy usernames
    # (e.g. "{}", "|", "*"), keeping common name punctuation (apostrophe, hyphen, period)
    cleaned = re.sub(r"[^A-Za-z0-9 '\-.]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


async def get_bounty_poster(
    update: Update, user: User, telegram_user=None
) -> str:
    """
    Gets the bounty poster of a user
    :param update: Telegram update
    :param user: The user to get the poster of
    :param telegram_user: Optional Telegram user to fetch the portrait for
    :return: The path to the poster
    """

    from src.service.user_service import get_user_profile_photo

    raw_first_name = (user.tg_first_name or "").strip()
    raw_last_name = (user.tg_last_name or "").strip()

    # If the name is written in a script we can show as-is (see NATIVE_SCRIPT_FONT_MAP), skip
    # the Latin sanitization/transliteration entirely. The poster is generated with a blank
    # placeholder name below, then the real name is drawn natively over it afterward.
    # Only attempted if this environment's Pillow build actually supports it (see RAQM_AVAILABLE)
    native_script = None
    if RAQM_AVAILABLE:
        native_script = get_native_script(raw_first_name) or get_native_script(raw_last_name)
    native_script_text = f"{raw_first_name} {raw_last_name}".strip() if native_script else None

    if native_script:
        poster_first_name = " "
        poster_last_name = " "
    else:
        # The underlying poster generator renders names as "LAST FIRST".
        # Swap inputs so the poster displays "FIRST LAST".
        poster_first_name = get_bounty_poster_name(raw_first_name)
        poster_last_name = get_bounty_poster_name(raw_last_name)

        # If sanitization stripped everything (e.g. an emoji-only name), fall back to a
        # placeholder rather than showing a blank name on the poster
        if not poster_first_name and not poster_last_name:
            poster_first_name = BOUNTY_POSTER_FALLBACK_NAME

    portrait = await get_user_profile_photo(update, telegram_user)

    return await asyncio.to_thread(
        _generate_poster_sync,
        user,
        portrait,
        poster_first_name,
        poster_last_name,
        native_script,
        native_script_text,
        raw_first_name,
        raw_last_name,
    )


def _generate_poster_sync(
    user: User,
    portrait,
    poster_first_name: str,
    poster_last_name: str,
    native_script: str | None,
    native_script_text: str | None,
    raw_first_name: str,
    raw_last_name: str,
) -> str:
    """
    Does the actual CPU-bound poster generation (font loading/shaping, image compositing,
    resizing, disk I/O) synchronously. Only ever called through asyncio.to_thread from
    get_bounty_poster, so this blocking work runs on a separate thread instead of stalling the
    single-threaded event loop (and with it, every other scheduled task in the Bot - e.g. a
    game's start countdown - for however long generation takes) while it runs
    :return: The path to the generated poster
    """

    from src.service.user_service import get_boss_type

    wanted_poster = WantedPoster(
        portrait=portrait,
        first_name=poster_last_name,
        last_name=poster_first_name,
        bounty=user.bounty,
    )

    capture_condition: CaptureCondition = CaptureCondition.DEAD_OR_ALIVE
    effects: list[Effect] = []
    stamp: Stamp | None = None

    if user_has_eaten_devil_fruit(user):
        capture_condition = CaptureCondition.ONLY_ALIVE

    boss_type: BossType = get_boss_type(user)
    if boss_type not in [None, BossType.WARLORD]:
        capture_condition = CaptureCondition.ONLY_DEAD

    # Warlord, add frost effect and warlord stamp
    match boss_type:
        # Warlord, add frost effect and warlord stamp
        case BossType.WARLORD:  # Frost effect and warlord stamp
            effects.append(Effect.FROST)
            stamp = Stamp.WARLORD

        # Admin, Pirate King or Legendary Pirate, add lightning effect
        case BossType.ADMIN | BossType.PIRATE_KING | BossType.LEGENDARY_PIRATE:
            effects.append(Effect.LIGHTNING)

            # Admin, add "Flee on sight" stamp
            if boss_type is BossType.ADMIN:
                stamp = Stamp.FLEE_ON_SIGHT
            # Pirate King and Legendary Pirate, add "Do not engage" stamp
            else:
                stamp = Stamp.DO_NOT_ENGAGE

    poster_path = wanted_poster.generate(
        output_poster_path=generate_temp_file_path(c.BOUNTY_POSTER_EXTENSION),
        portrait_vertical_align=VerticalAlignment.TOP,
        capture_condition=capture_condition,
        effects=effects,
        stamp=stamp,
        # Removed the default 16 character cap: beyond it, the library's old fallback logic
        # could end up displaying a blank name (see get_bounty_poster_name above for why
        # names could exceed it unnecessarily). The poster's name plate already auto-scales
        # text that doesn't fit, so longer names just render smaller instead of disappearing
        full_name_max_length=None,
    )

    # Draw the real name in its original script over the placeholder used above
    if native_script:
        try:
            name_component = _build_mixed_script_name_component(native_script_text)
            poster_image = Image.open(poster_path).convert("RGB")
            poster_image.paste(name_component, (0, BOUNTY_POSTER_NAME_START_Y), name_component)
            poster_image.save(poster_path)
        except Exception as e:
            # Don't let a native-script rendering failure break the whole poster -- regenerate
            # it using the normal Latin transliteration fallback instead
            logging.error(f"Native script name rendering failed, falling back to Latin: {e}")

            fallback_first_name = get_bounty_poster_name(raw_first_name)
            fallback_last_name = get_bounty_poster_name(raw_last_name)
            if not fallback_first_name and not fallback_last_name:
                fallback_first_name = BOUNTY_POSTER_FALLBACK_NAME

            fallback_poster = WantedPoster(
                portrait=wanted_poster.portrait,
                first_name=fallback_last_name,
                last_name=fallback_first_name,
                bounty=user.bounty,
            )
            poster_path = fallback_poster.generate(
                output_poster_path=poster_path,
                portrait_vertical_align=VerticalAlignment.TOP,
                capture_condition=capture_condition,
                effects=effects,
                stamp=stamp,
                full_name_max_length=None,
            )

    return poster_path


def get_bounty_poster_limit(leaderboard_user: LeaderboardUser) -> int:
    """
    Gets the bounty poster limit of a user by their leaderboard position
    :param leaderboard_user: The user to get the bounty poster limit of
    :return: The bounty poster limit of the user
    """

    leaderboard_rank: LeaderboardRank = get_rank_by_index(leaderboard_user.rank_index)
    return leaderboard_rank.bounty_poster_limit


async def reset_bounty_poster_limit(reset_previous_leaderboard: bool = False) -> None:
    """
    Resets the bounty poster limit

    :param reset_previous_leaderboard: If to reset the limit for users if the previous leaderboard
    """

    from src.service.leaderboard_service import get_leaderboard

    if reset_previous_leaderboard:
        # Reset the limit for users
        previous_leaderboard: Leaderboard = get_leaderboard(1)
        previous_leaderboard_users_id = LeaderboardUser.select(LeaderboardUser.user).where(
            LeaderboardUser.leaderboard == previous_leaderboard
        )
        if previous_leaderboard is not None:
            User.update(bounty_poster_limit=0).where(
                User.id.in_(previous_leaderboard_users_id)
            ).execute()

    # Reset the limit for the current leaderboard users
    current_leaderboard: Leaderboard = get_leaderboard()
    if current_leaderboard is not None:
        for leaderboard_user in current_leaderboard.leaderboard_users:
            leaderboard_user: LeaderboardUser = leaderboard_user

            User.update(bounty_poster_limit=get_bounty_poster_limit(leaderboard_user)).where(
                User.id == leaderboard_user.user
            ).execute()
