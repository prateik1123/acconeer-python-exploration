# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved
from __future__ import annotations

import typing as t

import pytest

from acconeer.exptool.a121._core.peripherals import ExplorationProtocol
from acconeer.exptool.a121._core.peripherals.communication.exploration_protocol import messages


class TestSetBaudrateResponse:
    @pytest.fixture
    def valid_server_response(self) -> dict[str, t.Any]:
        return {"status": "ok", "payload_size": 0, "message": "set baudrate"}

    @pytest.fixture
    def invalid_server_response(self) -> dict[str, t.Any]:
        return {"status": "ok"}

    def test_parse(
        self, valid_server_response: dict[str, t.Any], invalid_server_response: dict[str, t.Any]
    ) -> None:
        assert (
            type(ExplorationProtocol.parse_message(valid_server_response, bytes()))
            == messages.SetBaudrateResponse
        )
        _ = messages.SetBaudrateResponse.parse(valid_server_response, bytes())

        with pytest.raises(messages.ParseError):
            messages.SetBaudrateResponse.parse(invalid_server_response, bytes())

    def test_apply(self) -> None:
        pytest.skip("SetBaudrateResponse has a NO-OP apply")
