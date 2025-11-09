from dataclasses import dataclass, asdict
from typing import Optional

import colorblind_plugin as lib
import decky
from settings import SettingsManager


@dataclass
class CorrectionConfig:
    enabled: bool
    cb_type: lib.CBType
    operation: lib.Operation
    strength: float
    lut_size: int

    def to_dict(self):
        return asdict(self)


class ColorBlindSettings:
    settingsMgr = SettingsManager("settings", settings_directory=decky.DECKY_PLUGIN_SETTINGS_DIR)

    def __init__(self):
        self.settingsMgr.read()

    @staticmethod
    def _config_scope(app_id: Optional[str] = None) -> str:
        if app_id is None:
            return "correction.GLOBAL"
        else:
            return f"correction.{app_id}"

    def update_game_config(self, config: CorrectionConfig, app_id: Optional[str] = None):
        key_scope = self._config_scope(app_id)
        self.settingsMgr.setSetting(f"{key_scope}.enabled", config.enabled)
        self.settingsMgr.setSetting(f"{key_scope}.cb_type", config.cb_type)
        self.settingsMgr.setSetting(f"{key_scope}.operation", config.operation)
        self.settingsMgr.setSetting(f"{key_scope}.strength", config.strength)
        self.settingsMgr.setSetting(f"{key_scope}.lut_size", config.lut_size)
        self.settingsMgr.commit()

    def get_game_config(self, app_id: Optional[str] = None) -> CorrectionConfig:
        key_scope = self._config_scope(app_id)
        enabled = self.settingsMgr.getSetting(f"{key_scope}.enabled", True)
        cb_type = self.settingsMgr.getSetting(f"{key_scope}.cb_type", "deuteranope")
        operation = self.settingsMgr.getSetting(f"{key_scope}.operation", "hue_shift")
        strength = self.settingsMgr.getSetting(f"{key_scope}.strength", 0.8)
        lut_size = self.settingsMgr.getSetting(f"{key_scope}.lut_size", 32)

        return CorrectionConfig(enabled, cb_type, operation, strength, lut_size)
