"""
Configuration manager for the colorblind correction plugin.

Manages global plugin settings and per-game LUT configurations using INI files.
"""

import decky
import configparser
import os
from dataclasses import dataclass
from typing import Optional

# Import types from lut_generator
from colorblind_plugin import CBType, Operation


@dataclass
class CorrectionConfig:
    """Strong-typed configuration for colorblind correction settings."""
    enabled: bool
    cb_type: CBType
    operation: Operation
    strength: float
    lut_size: int


class ConfigManager:
    """Manages plugin configuration with global and per-game settings."""

    CONFIG_FILENAME = "config.ini"
    GLOBAL_GAME_ID = "GLOBAL"

    def __init__(self):
        """Initialize config manager and load or create config file."""
        self.config_path = os.path.join(
            decky.DECKY_PLUGIN_SETTINGS_DIR,
            self.CONFIG_FILENAME
        )
        self.config = configparser.ConfigParser()

        # Load existing config or create with defaults
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
            # Ensure required sections exist
            if not self.config.has_section('global'):
                self.config.add_section('global')
            if not self.config.has_section(f'game_{self.GLOBAL_GAME_ID}'):
                self._set_game_section(self.GLOBAL_GAME_ID, self._get_default_config())
                self._save()
        else:
            # Create new config with defaults
            self._create_default_config()

    def _create_default_config(self):
        """Create a new config file with default values."""
        # Add global section (for plugin-level settings)
        self.config.add_section('global')

        # Add default game config under game_GLOBAL
        self._set_game_section(self.GLOBAL_GAME_ID, self._get_default_config())

        # Save to disk
        self._save()

    def _get_default_config(self) -> CorrectionConfig:
        """Get default correction configuration."""
        return CorrectionConfig(
            enabled=True,
            cb_type="deuteranope",
            operation="correct",
            strength=1.0,
            lut_size=32
        )

    def _get_game_section_name(self, game_id: str) -> str:
        """Get the INI section name for a game ID."""
        return f"game_{game_id}"

    def _get_game_section(self, game_id: str) -> Optional[CorrectionConfig]:
        """Read game config from INI section, returns None if not found."""
        section_name = self._get_game_section_name(game_id)

        if not self.config.has_section(section_name):
            return None

        section = self.config[section_name]

        return CorrectionConfig(
            enabled=section.getboolean('enabled', True),
            cb_type=section.get('cb_type', 'protanope'),
            operation=section.get('operation', 'correct'),
            strength=section.getfloat('strength', 1.0),
            lut_size=section.getint('lut_size', 32)
        )

    def _set_game_section(self, game_id: str, config: CorrectionConfig):
        """Write game config to INI section."""
        section_name = self._get_game_section_name(game_id)

        if not self.config.has_section(section_name):
            self.config.add_section(section_name)

        section = self.config[section_name]
        section['enabled'] = str(config.enabled)
        section['cb_type'] = config.cb_type
        section['operation'] = config.operation
        section['strength'] = str(config.strength)
        section['lut_size'] = str(config.lut_size)

    def _save(self):
        """Persist configuration to disk."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        with open(self.config_path, 'w') as f:
            self.config.write(f)

    def get_config(self, game_id: Optional[str] = None) -> CorrectionConfig:
        """
        Get correction configuration for a game or global default.

        Args:
            game_id: Optional game identifier (e.g., Steam app ID).
                     If None or not found, returns GLOBAL config.

        Returns:
            CorrectionConfig for the specified game or global default.
        """
        # If no game_id specified, return GLOBAL
        if game_id is None:
            game_id = self.GLOBAL_GAME_ID

        # Try to get game-specific config
        game_config = self._get_game_section(game_id)

        # If game config exists, return it
        if game_config is not None:
            return game_config

        # Otherwise fall back to GLOBAL
        global_config = self._get_game_section(self.GLOBAL_GAME_ID)

        # If GLOBAL doesn't exist (shouldn't happen), return defaults
        if global_config is None:
            return self._get_default_config()

        return global_config

    def set_config(self, config: CorrectionConfig, game_id: Optional[str] = None):
        """
        Set correction configuration for a game or global default.

        Args:
            config: CorrectionConfig object with settings to save.
            game_id: Optional game identifier. If None, updates GLOBAL config.
        """
        if game_id is None:
            game_id = self.GLOBAL_GAME_ID

        self._set_game_section(game_id, config)
        self._save()

    def reset(self, game_id: Optional[str] = None):
        """
        Reset configuration to defaults.

        Args:
            game_id: Optional game identifier.
                     If None, resets ALL configs (GLOBAL and all games).
                     If specified, resets only that game's config.
        """
        if game_id is None:
            # Reset everything - clear all sections and recreate defaults
            self.config.clear()
            self._create_default_config()
        else:
            # Reset specific game to default config
            default_config = self._get_default_config()
            self._set_game_section(game_id, default_config)
            self._save()
