"""Card-action addressing: the synthetic event must carry a usable message id
and the topic it came from.

Why this file exists (gonzo fork). Lark Topic-mode has no per-message
addressing — a reply inside a topic reports ``parent_id == root_id``, always
the topic root — so cards are the only way to say "this deliverable, not that
one". That makes the card path load-bearing rather than decorative
(docs/architecture/decisions/0002-dinh-vi-trong-lark-va-va-adapter.md).

Two defects observed against a live Lark tenant on 2026-07-26:

  * ``message_id`` was set to the card action ``token`` (a ``c-…`` value).
    Every downstream reaction/reply call then failed with Lark 99992354
    ("not a valid open_message_id"), including the plain-text fallback, so the
    bot went silent instead of degrading.
  * ``thread_id`` was hardcoded ``None``, so the agent could not tell which
    topic a card belonged to and could not answer back into it.

Both are recoverable from ``context.open_message_id``, which the event already
carries next to the ``open_chat_id`` the adapter was already reading.
"""

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_repo = str(Path(__file__).resolve().parents[2])
if _repo not in sys.path:
    sys.path.insert(0, _repo)


def _ensure_feishu_mocks():
    if importlib.util.find_spec("lark_oapi") is None and "lark_oapi" not in sys.modules:
        mod = MagicMock()
        for name in (
            "lark_oapi", "lark_oapi.api.im.v1",
            "lark_oapi.event", "lark_oapi.event.callback_type",
        ):
            sys.modules.setdefault(name, mod)
    if importlib.util.find_spec("aiohttp") is None and "aiohttp" not in sys.modules:
        aio = MagicMock()
        sys.modules.setdefault("aiohttp", aio)
        sys.modules.setdefault("aiohttp.web", aio.web)


_ensure_feishu_mocks()

from gateway.config import PlatformConfig
from plugins.platforms.feishu.adapter import FeishuAdapter

CARD_TOKEN = "c-67998aca825a66fd1499f7097ceec9a85718c275"
CARD_MESSAGE_ID = "om_x100b69690018b4a0eea489bfb1aaeb4"
TOPIC_ID = "omt_19005c24758f1946"
CHAT_ID = "oc_241eeec211ec3b4bb6e90368a2e695e6"


def _make_adapter() -> FeishuAdapter:
    adapter = FeishuAdapter(PlatformConfig(enabled=True))
    adapter._client = MagicMock()
    return adapter


def _card_event(*, with_message_id: bool = True) -> SimpleNamespace:
    """A card button click as Lark actually delivers it.

    ``open_message_id`` sits in ``context`` alongside ``open_chat_id``; the
    ``token`` is a card identifier and is NOT a message id.
    """
    context_fields = {"open_chat_id": CHAT_ID}
    if with_message_id:
        context_fields["open_message_id"] = CARD_MESSAGE_ID
    return SimpleNamespace(
        event=SimpleNamespace(
            token=CARD_TOKEN,
            context=SimpleNamespace(**context_fields),
            operator=SimpleNamespace(open_id="ou_d8ae79a451ae27e360ae6dfc6783d0ee"),
            action=SimpleNamespace(tag="button", value={"item": "creative-2"}),
        ),
    )


async def _capture_synthetic_event(adapter, data):
    """Run the handler and return the MessageEvent it would have dispatched."""
    captured = {}

    async def _fake_guard(event):
        captured["event"] = event

    adapter._resolve_sender_profile = AsyncMock(
        return_value={"user_id": "1d13c1ff", "user_name": "Khánh", "user_id_alt": None}
    )
    adapter.get_chat_info = AsyncMock(return_value={"name": "Hermes#Test"})
    adapter._handle_message_with_guards = _fake_guard
    adapter._resolve_thread_id_for_message = AsyncMock(return_value=TOPIC_ID)

    await adapter._handle_card_action_event(data)
    return captured.get("event")


@pytest.mark.asyncio
async def test_message_id_is_the_card_message_not_the_card_token():
    """Lark rejects a ``c-…`` token wherever an ``om_…`` message id is required.

    Passing the token through made every send fail with 99992354 — including
    the fallback — so the bot could not even report the error.
    """
    event = await _capture_synthetic_event(_make_adapter(), _card_event())

    assert event is not None, "handler dispatched no event"
    assert event.message_id == CARD_MESSAGE_ID
    assert not event.message_id.startswith("c-"), (
        "card token leaked into message_id; Lark will reject every reaction and reply"
    )


@pytest.mark.asyncio
async def test_source_carries_the_topic_the_card_lives_in():
    """Without thread_id the agent cannot answer back into the right topic."""
    event = await _capture_synthetic_event(_make_adapter(), _card_event())

    assert event.source.thread_id == TOPIC_ID


@pytest.mark.asyncio
async def test_button_value_survives_intact():
    """The whole point of the card path: which deliverable was clicked."""
    event = await _capture_synthetic_event(_make_adapter(), _card_event())

    assert "creative-2" in event.text, f"button value lost: {event.text!r}"


@pytest.mark.asyncio
async def test_missing_open_message_id_degrades_without_a_poisoned_id():
    """Older payloads may omit open_message_id.

    Falling back to the ``c-…`` token would be worse than having nothing: it
    produces a value that *looks* like an id and fails at the API boundary.
    """
    event = await _capture_synthetic_event(
        _make_adapter(), _card_event(with_message_id=False)
    )

    assert event is not None
    assert not (event.message_id or "").startswith("c-")
