from __future__ import annotations

import abc
from typing import Iterable

from ._client_info import ClientInfo
from ._metadata import Metadata
from ._result import Result
from ._server_info import ServerInfo
from ._session_config import SessionConfig


class Record(abc.ABC):
    @property
    @abc.abstractmethod
    def client_info(self) -> ClientInfo:
        ...

    @property
    @abc.abstractmethod
    def extended_metadata(self) -> list[dict[int, Metadata]]:
        ...

    @property
    @abc.abstractmethod
    def extended_results(self) -> Iterable[list[dict[int, Result]]]:
        ...

    @property
    @abc.abstractmethod
    def lib_version(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def num_frames(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def server_info(self) -> ServerInfo:
        ...

    @property
    @abc.abstractmethod
    def session_config(self) -> SessionConfig:
        ...

    @property
    @abc.abstractmethod
    def timestamp(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def uuid(self) -> str:
        ...

    @property
    def metadata(self) -> Metadata:
        raise NotImplementedError

    def close(self) -> None:
        pass
