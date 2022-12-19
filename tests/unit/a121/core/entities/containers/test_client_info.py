# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved

from __future__ import annotations

from typing import Tuple

import pytest

from acconeer.exptool.a121 import ClientInfo
from acconeer.exptool.utils import SerialDevice, USBDevice  # type: ignore[import]


CLIENT_INFO_PARAMETRIZE = [
    (
        dict(ip_address="addr"),
        {
            "serial": None,
            "usb": None,
            "socket": {"ip_address": "addr"},
            "mock": None,
        },
    ),
    (
        dict(serial_port="port", override_baudrate=0),
        {
            "serial": {"port": "port", "override_baudrate": 0, "serial_number": None},
            "usb": None,
            "socket": None,
            "mock": None,
        },
    ),
    (
        dict(usb_device=True),
        {
            "serial": None,
            "socket": None,
            "mock": None,
            "usb": {"vid": None, "pid": None, "serial_number": None},
        },
    ),
    (
        dict(usb_device="1234"),
        {
            "serial": None,
            "usb": {"vid": None, "pid": None, "serial_number": "1234"},
            "socket": None,
            "mock": None,
        },
    ),
    (
        dict(mock=True),
        {
            "serial": None,
            "usb": None,
            "socket": None,
            "mock": {},
        },
    ),
]


@pytest.fixture(params=CLIENT_INFO_PARAMETRIZE)
def client_info_fixture(request: pytest.FixtureRequest) -> Tuple[ClientInfo, dict]:
    from_open_args = request.param[0]
    client_info_dict = request.param[1]
    return (ClientInfo._from_open(**from_open_args), client_info_dict)


def test_to_dict(client_info_fixture: Tuple[ClientInfo, dict]) -> None:
    client_info = client_info_fixture[0]
    client_info_dict = client_info_fixture[1]
    assert client_info.to_dict() == client_info_dict


def test_from_dict(client_info_fixture: Tuple[ClientInfo, dict]) -> None:
    client_info = client_info_fixture[0]
    client_info_dict = client_info_fixture[1]
    assert ClientInfo.from_dict(client_info_dict) == client_info


def test_to_from_dict_equality(client_info_fixture: Tuple[ClientInfo, dict]) -> None:
    client_info = client_info_fixture[0]
    assert client_info == ClientInfo.from_dict(client_info.to_dict())


def test_from_dict_extra_kwarg(client_info_fixture: Tuple[ClientInfo, dict]) -> None:
    client_info_dict = client_info_fixture[1]
    client_info_dict["extra"] = "kwarg"
    with pytest.raises(TypeError):
        ClientInfo.from_dict(client_info_dict)


def test_to_from_json_equality(client_info_fixture: Tuple[ClientInfo, dict]) -> None:
    client_info = client_info_fixture[0]
    assert client_info == ClientInfo.from_json(client_info.to_json())


def test_usb_device_display_name() -> None:
    usb_name = "DEV_NAME"
    usb_serial = "123456"

    usb_device = USBDevice(vid=0x4CC0, pid=0xAEE3, serial=None, name=usb_name, recognized=True)
    assert usb_device.display_name() == usb_name

    usb_device = USBDevice(
        vid=0x4CC0, pid=0xAEE3, serial=usb_serial, name=usb_name, recognized=True
    )
    assert usb_device.display_name() == f"{usb_name} ({usb_serial})"

    usb_device = USBDevice(
        vid=0x4CC0, pid=0xAEE3, serial=usb_serial, name=usb_name, unflashed=True, recognized=True
    )
    assert usb_device.display_name() == f"Unflashed {usb_name}"

    usb_device = USBDevice(
        vid=0x4CC0, pid=0xAEE3, serial=usb_serial, name=usb_name, accessible=False, recognized=True
    )
    assert usb_device.display_name() == f"{usb_name} (inaccessible)"

    usb_device = USBDevice(
        vid=0x4CC0,
        pid=0xAEE3,
        serial=usb_serial,
        name=usb_name,
        unflashed=True,
        accessible=False,
        recognized=True,
    )
    assert usb_device.display_name() == f"{usb_name} (inaccessible)"


def test_serial_device_display_name() -> None:
    device_name = "DEV_NAME"
    port_name = "/dev/ttyACM0"
    port_serial_number = "abcdef"

    serial_device = SerialDevice(port=port_name, recognized=True)
    assert serial_device.display_name() == f"{port_name}"

    serial_device = SerialDevice(port=port_name, serial=port_serial_number, recognized=True)
    assert serial_device.display_name() == f"{port_name} ({port_serial_number})"

    serial_device = SerialDevice(port=port_name, serial=port_serial_number, recognized=True)
    assert serial_device.display_name() == f"{port_name} ({port_serial_number})"

    serial_device = SerialDevice(
        name=device_name, port=port_name, serial=port_serial_number, recognized=True
    )
    assert serial_device.display_name() == f"{device_name} {port_name} ({port_serial_number})"

    serial_device = SerialDevice(name=device_name, port=port_name, recognized=True)
    assert serial_device.display_name() == f"{device_name} {port_name}"

    serial_device = SerialDevice(
        name=device_name,
        port=port_name,
        serial=port_serial_number,
        recognized=True,
        unflashed=True,
    )
    assert serial_device.display_name() == f"Unflashed {device_name} {port_name}"
