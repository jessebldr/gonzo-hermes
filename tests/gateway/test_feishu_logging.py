"""Security boundary tests for logs emitted by the official Lark SDK."""

from __future__ import annotations

import io
import logging


def test_lark_websocket_log_never_exposes_connection_credentials(monkeypatch):
    """Operators can debug the endpoint without persisting reusable credentials."""
    import agent.redact as redact

    # Importing the adapter is what wires the SDK logger into Hermes' security
    # boundary.  The guarantee must hold even when ordinary redaction is
    # disabled by operator preference.
    import plugins.platforms.feishu.adapter  # noqa: F401

    monkeypatch.setattr(redact, "_REDACT_ENABLED", False)

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    lark_logger = logging.getLogger("Lark")
    previous_level = lark_logger.level
    lark_logger.addHandler(handler)
    lark_logger.setLevel(logging.INFO)

    try:
        lark_logger.info(
            "connected to "
            "wss://msg-frontier-sg.larksuite.com/ws/v2?device_id=dev-123"
            "&aid=12&access_key=live-access-secret&ticket=live-ticket-secret"
            "&fpid=9"
        )
    finally:
        lark_logger.removeHandler(handler)
        lark_logger.setLevel(previous_level)

    output = stream.getvalue()
    assert "live-access-secret" not in output
    assert "live-ticket-secret" not in output
    assert "access_key=***" in output
    assert "ticket=***" in output
    assert "wss://msg-frontier-sg.larksuite.com/ws/v2" in output
    assert "device_id=dev-123" in output
    assert "aid=12" in output
    assert "fpid=9" in output
