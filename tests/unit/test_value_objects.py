"""Unit tests for domain value objects.

Tests immutability, validation invariants, and canonical representations for:
- Language
- AttackFamily
- Verdict
- Score
"""

import pytest

from nammakam_api.domain.value_objects.attack_family import AttackFamily
from nammakam_api.domain.value_objects.language import Language
from nammakam_api.domain.value_objects.score import Score
from nammakam_api.domain.value_objects.verdict import Verdict


class TestLanguageValueObject:
    def test_supported_languages_exist(self) -> None:
        assert Language.TELUGU.code == "te"
        assert Language.HINDI.code == "hi"
        assert Language.HINGLISH.code == "hinglish"
        assert Language.ENGLISH.code == "en-IN"

    def test_standard_locale_flag(self) -> None:
        assert Language.TELUGU.is_standard_locale is True
        assert Language.HINDI.is_standard_locale is True
        assert Language.ENGLISH.is_standard_locale is True
        # Hinglish is an internal code-mixed Indian language variant, not a BCP-47 standard
        assert Language.HINGLISH.is_standard_locale is False

    def test_lookup_by_code(self) -> None:
        assert Language.from_code("te") == Language.TELUGU
        assert Language.from_code("hi") == Language.HINDI
        assert Language.from_code("hinglish") == Language.HINGLISH
        assert Language.from_code("en-IN") == Language.ENGLISH

    def test_lookup_by_code_case_insensitive_and_aliases(self) -> None:
        assert Language.from_code("TE") == Language.TELUGU
        assert Language.from_code("EN-in") == Language.ENGLISH
        assert Language.from_code("en-in-hi") == Language.HINGLISH
        assert Language.from_code("hi-en") == Language.HINGLISH
        assert Language.from_code("hi-latn") == Language.HINGLISH

    def test_invalid_code_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unsupported language code"):
            Language.from_code("fr")

    def test_language_is_immutable(self) -> None:
        lang = Language.TELUGU
        with pytest.raises(AttributeError):
            lang.code = "new_code"  # type: ignore[misc]


class TestAttackFamilyValueObject:
    def test_core_banking_attack_families_exist(self) -> None:
        assert AttackFamily.AUTHORITY_IMPERSONATION.value == "authority_impersonation"
        assert AttackFamily.DIGITAL_ARREST.value == "digital_arrest"
        assert AttackFamily.URGENT_TRANSFER.value == "urgent_transfer"
        assert AttackFamily.CREDENTIAL_HARVESTING.value == "credential_harvesting"
        assert AttackFamily.BENEFICIARY_MANIPULATION.value == "beneficiary_manipulation"
        assert AttackFamily.CONTROL_BYPASS.value == "control_bypass"
        assert AttackFamily.UNAUTHORIZED_DISCLOSURE.value == "unauthorized_disclosure"
        assert AttackFamily.PROMPT_INJECTION.value == "prompt_injection"

    def test_lookup_by_identifier(self) -> None:
        assert (
            AttackFamily.from_identifier("digital_arrest")
            == AttackFamily.DIGITAL_ARREST
        )

    def test_invalid_identifier_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown attack family"):
            AttackFamily.from_identifier("unknown_attack")


class TestVerdictValueObject:
    def test_verdict_classifications(self) -> None:
        assert Verdict.SAFE.is_safe is True
        assert Verdict.UNSAFE_ACTION.is_safe is False
        assert Verdict.POLICY_VIOLATION.is_safe is False
        assert Verdict.MISSING_ESCALATION.is_safe is False
        assert Verdict.OVER_REFUSAL.is_safe is False

    def test_verdict_resilience_failure(self) -> None:
        assert Verdict.UNSAFE_ACTION.is_resilience_failure is True
        assert Verdict.POLICY_VIOLATION.is_resilience_failure is True
        assert Verdict.SAFE.is_resilience_failure is False


class TestScoreValueObject:
    def test_valid_score_creation(self) -> None:
        score = Score(0.85)
        assert score.value == 0.85
        assert score.as_percentage() == 85.0

    def test_boundary_scores(self) -> None:
        assert Score(0.0).value == 0.0
        assert Score(1.0).value == 1.0

    def test_out_of_bounds_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Score must be between 0.0 and 1.0"):
            Score(-0.01)
        with pytest.raises(ValueError, match="Score must be between 0.0 and 1.0"):
            Score(1.01)

    def test_non_numeric_score_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="must be numeric"):
            Score("0.5")  # type: ignore[arg-type]

    def test_score_comparisons(self) -> None:
        s1 = Score(0.4)
        s2 = Score(0.7)
        s3 = Score(0.4)
        assert s1 < s2
        assert s2 > s1
        assert s1 == s3
        assert s1 <= s3
        assert s2 >= s1
        assert (s1 == "0.4") is False

    def test_score_is_immutable(self) -> None:
        score = Score(0.5)
        with pytest.raises(AttributeError):
            score.value = 0.9  # type: ignore[misc]
