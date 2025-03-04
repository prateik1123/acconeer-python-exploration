# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved

from __future__ import annotations

from .app_model import PluginSpec


def load_default_plugins() -> list[PluginSpec]:
    from acconeer.exptool.a121.algo.bilateration._plugin import BILATERATION_PLUGIN
    from acconeer.exptool.a121.algo.breathing._ref_app_plugin import BREATHING_PLUGIN
    from acconeer.exptool.a121.algo.distance._detector_plugin import DISTANCE_DETECTOR_PLUGIN
    from acconeer.exptool.a121.algo.phase_tracking._plugin import PHASE_TRACKING_PLUGIN
    from acconeer.exptool.a121.algo.presence._detector_plugin import PRESENCE_DETECTOR_PLUGIN
    from acconeer.exptool.a121.algo.smart_presence._ref_app_plugin import SMART_PRESENCE_PLUGIN
    from acconeer.exptool.a121.algo.sparse_iq._plugin import SPARSE_IQ_PLUGIN
    from acconeer.exptool.a121.algo.speed._detector_plugin import SPEED_DETECTOR_PLUGIN
    from acconeer.exptool.a121.algo.surface_velocity._example_app_plugin import (
        SURFACE_VELOCITY_PLUGIN,
    )
    from acconeer.exptool.a121.algo.tank_level._plugin import TANK_LEVEL_PLUGIN
    from acconeer.exptool.a121.algo.touchless_button._plugin import TOUCHLESS_BUTTON_PLUGIN
    from acconeer.exptool.a121.algo.vibration._plugin import VIBRATION_PLUGIN

    # Please keep in lexicographical order
    return [
        BILATERATION_PLUGIN,
        BREATHING_PLUGIN,
        DISTANCE_DETECTOR_PLUGIN,
        PHASE_TRACKING_PLUGIN,
        PRESENCE_DETECTOR_PLUGIN,
        SMART_PRESENCE_PLUGIN,
        SPARSE_IQ_PLUGIN,
        SURFACE_VELOCITY_PLUGIN,
        TANK_LEVEL_PLUGIN,
        TOUCHLESS_BUTTON_PLUGIN,
        VIBRATION_PLUGIN,
        SPEED_DETECTOR_PLUGIN,
    ]
