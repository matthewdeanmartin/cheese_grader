"""
Sett up the whats_that_code call
"""
from typing import List, Tuple

from whats_that_code.election import guess_language_all_methods
from whats_that_code.known_languages import FILE_EXTENSIONS

from so_pip.settings import POSSIBLE_LANGUAGES


def guess_language_and_extension(
    code: str, surrounding_text: str = "", tags: List[str] = None
) -> Tuple[str, str]:
    """Guess language and extension"""
    if not code:
        return "", ""
    if not tags:
        raise TypeError("Missing tags")
    result = guess_language_all_methods(
        code,
        file_name="",
        surrounding_text=surrounding_text,
        tags=tags,
        priors=POSSIBLE_LANGUAGES,
    )
    if result:
        if result in FILE_EXTENSIONS:
            # take top extension option
            return FILE_EXTENSIONS[result][0], result
        return f".{result}", result

    return "", ""
