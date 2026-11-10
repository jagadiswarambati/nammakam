"""Language Value Object.

Defines supported Indian evaluation languages: Telugu, Hindi, Hinglish, and Indian English.
Implemented as an immutable enumeration.

Note on Hinglish:
Hinglish uses an internal, explicit identifier ('hinglish') representing code-mixed
Hindi and Indian English (typically Hindi vocabulary rendered in Latin script with English
financial terminology). It is not an official or standard BCP-47 language tag.
Telugu ('te'), Hindi ('hi'), and Indian English ('en-IN') use standard language tags.
"""

from enum import Enum
from typing import Self


class Language(Enum):
    """Supported languages for banking agent safety evaluation."""

    TELUGU = ("te", "Telugu", "తెలుగు", True)
    HINDI = ("hi", "Hindi", "हिन्दी", True)
    HINGLISH = ("hinglish", "Hinglish", "Hinglish (Code-Mixed Hindi-English)", False)
    ENGLISH = ("en-IN", "English", "Indian English", True)

    def __init__(
        self,
        code: str,
        display_name: str,
        native_name: str,
        is_standard_locale: bool,
    ) -> None:
        self._code = code
        self._display_name = display_name
        self._native_name = native_name
        self._is_standard_locale = is_standard_locale

    @property
    def code(self) -> str:
        """Returns the canonical language code or internal identifier."""
        return self._code

    @property
    def display_name(self) -> str:
        """Returns the standard English display name."""
        return self._display_name

    @property
    def native_name(self) -> str:
        """Returns the native or localized description."""
        return self._native_name

    @property
    def is_standard_locale(self) -> bool:
        """Indicates whether the language code corresponds to a formal BCP-47 / ISO locale.

        Returns False for Hinglish, which is an internal code-mixed dialect identifier.
        """
        return self._is_standard_locale

    @classmethod
    def from_code(cls, code: str) -> Self:
        """Resolves a Language enum from a code or alias string (case-insensitive).

        Args:
            code: Language code string (e.g. 'te', 'hi', 'hinglish', 'en-IN').

        Returns:
            The matching Language enum instance.

        Raises:
            ValueError: If the language code is unsupported.
        """
        normalized = code.strip().lower()

        # Check primary codes
        for member in cls:
            if member.code.lower() == normalized:
                return member

        # Recognized aliases
        aliases: dict[str, Language] = {
            "en-in-hi": cls.HINGLISH,
            "hi-latn": cls.HINGLISH,
            "hi-en": cls.HINGLISH,
            "en-hi": cls.HINGLISH,
            "te-in": cls.TELUGU,
            "hi-in": cls.HINDI,
            "en": cls.ENGLISH,
        }

        if normalized in aliases:
            return aliases[normalized]

        supported_codes = [m.code for m in cls]
        raise ValueError(
            f"Unsupported language code: '{code}'. Supported canonical identifiers: {supported_codes}"
        )
