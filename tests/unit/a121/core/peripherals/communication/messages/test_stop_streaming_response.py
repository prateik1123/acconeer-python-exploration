# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved
from __future__ import annotations

import typing as t

import pytest

from acconeer.exptool.a121._core.peripherals import ExplorationProtocol
from acconeer.exptool.a121._core.peripherals.communication.exploration_protocol import messages


class TestStopStreamingResponse:
    @pytest.fixture
    def valid_server_response(self) -> dict[str, t.Any]:
        return {"status": "stop", "payload_size": 0, "message": "Stop streaming."}

    @pytest.fixture
    def invalid_server_response(self) -> dict[str, t.Any]:
        return {"status": "ok"}

    def test_parse(
        self, valid_server_response: dict[str, t.Any], invalid_server_response: dict[str, t.Any]
    ) -> None:
        assert (
            type(ExplorationProtocol.parse_message(valid_server_response, bytes()))
            == messages.StopStreamingResponse
        )
        _ = messages.StopStreamingResponse.parse(valid_server_response, bytes())

        with pytest.raises(messages.ParseError):
            messages.StopStreamingResponse.parse(invalid_server_response, bytes())
