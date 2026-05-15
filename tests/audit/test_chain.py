from __future__ import annotations

from mohizarbot.audit.log import (
    AuditEntry,
    compute_hmac,
    create_entry,
    genesis_hmac,
    verify_chain,
)


def test_genesis_hmac_is_64_zeros() -> None:
    assert genesis_hmac() == "0" * 64


def test_append_three_entries_verifies() -> None:
    key = b"test-key-for-hmac"

    e1 = create_entry(
        key,
        previous_hmac=genesis_hmac(),
        chat_id=1,
        user_id=100,
        intent_json='{"type": "send_message"}',
        decision="allowed",
        reasoning_summary="test entry 1",
    )

    e2 = create_entry(
        key,
        previous_hmac=e1.hmac,
        chat_id=1,
        user_id=101,
        intent_json='{"type": "send_message"}',
        decision="allowed",
        reasoning_summary="test entry 2",
    )

    e3 = create_entry(
        key,
        previous_hmac=e2.hmac,
        chat_id=1,
        user_id=102,
        intent_json='{"type": "send_message"}',
        decision="denied",
        reasoning_summary="test entry 3",
    )

    chain = [e1, e2, e3]
    assert verify_chain(key, chain) is True


def test_mutating_entry_breaks_verification() -> None:
    key = b"test-key-for-hmac"

    e1 = create_entry(
        key,
        previous_hmac=genesis_hmac(),
        chat_id=1,
        user_id=100,
        intent_json='{"type": "send_message"}',
        decision="allowed",
        reasoning_summary="original",
    )

    e2 = create_entry(
        key,
        previous_hmac=e1.hmac,
        chat_id=1,
        user_id=101,
        intent_json='{"type": "send_message"}',
        decision="allowed",
        reasoning_summary="original",
    )

    # Mutate e1's decision
    e1.decision = "denied"

    assert verify_chain(key, [e1, e2]) is False


def test_mutating_entry_content_breaks_verification() -> None:
    key = b"test-key-for-hmac"

    e1 = create_entry(
        key,
        previous_hmac=genesis_hmac(),
        chat_id=1,
        user_id=100,
        intent_json='{"type": "send_message"}',
        decision="allowed",
        reasoning_summary="original",
    )

    e2 = create_entry(
        key,
        previous_hmac=e1.hmac,
        chat_id=1,
        user_id=101,
        intent_json='{"type": "send_message"}',
        decision="allowed",
        reasoning_summary="original",
    )

    # Mutate e2's intent_json
    e2.intent_json = '{"type": "ban_user"}'

    assert verify_chain(key, [e1, e2]) is False


def test_chain_link_break_is_detected() -> None:
    key = b"test-key-for-hmac"

    e1 = create_entry(
        key,
        previous_hmac=genesis_hmac(),
        chat_id=1,
        user_id=100,
        intent_json='{"type": "send_message"}',
        decision="allowed",
        reasoning_summary="entry 1",
    )

    e2 = create_entry(
        key,
        previous_hmac=e1.hmac,
        chat_id=1,
        user_id=101,
        intent_json='{"type": "send_message"}',
        decision="allowed",
        reasoning_summary="entry 2",
    )

    # Break the chain link by resetting the previous_hmac to genesis
    e2.previous_hmac = genesis_hmac()

    assert verify_chain(key, [e1, e2]) is False


def test_empty_chain_verifies() -> None:
    key = b"test-key-for-hmac"
    assert verify_chain(key, []) is True


def test_create_entry_without_previous_hmac_raises() -> None:
    import pytest

    key = b"test-key"
    with pytest.raises(ValueError, match="previous_hmac must be set"):
        compute_hmac(
            key,
            AuditEntry(
                timestamp="2024-01-01T00:00:00Z",
                chat_id=1,
                user_id=100,
                intent_json="{}",
                decision="allowed",
                reasoning_summary="test",
                previous_hmac="",
            ),
        )
