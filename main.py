import json
import os
import subprocess
from typing import Optional
import decky
import asyncio
import colorblind_plugin as lib
from dataclasses import asdict

from colorblind_plugin.plugin_config import ColorBlindSettings


def _get_clean_env():
    """Get environment with cleared LD_LIBRARY_PATH to fix decky-loader subprocess issues"""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ""
    # XDG_RUNTIME_DIR must be set otherwise gamescopectl won't be able to detect the display
    env["XDG_RUNTIME_DIR"] = "/run/user/1000"

    return env


class Plugin:
    _config = ColorBlindSettings()
    _clean_env = _get_clean_env()

    async def apply_configuration(self, app_id: Optional[str]):
        """Apply the current configuration by generating and setting LUT."""
        correction_config = self._config.get_game_config(app_id)

        if not correction_config.enabled:
            decky.logger.info("Correction disabled, skipping LUT application")
            self.reset_look()
            return

        lut_path = os.path.join(decky.DECKY_PLUGIN_RUNTIME_DIR, "lut.cube")
        decky.logger.info(f"Generating LUT: {correction_config.cb_type}, {correction_config.operation}, strength={correction_config.strength}")

        lib.lut_generator.generate_lut(
            cb_type=correction_config.cb_type,
            operation=correction_config.operation,
            strength=correction_config.strength,
            output_path=lut_path,
            lut_size=correction_config.lut_size
        )
        self.set_look(lut_path)
        decky.logger.info(f"LUT applied successfully")

    async def update_configuration(self, enabled: bool, cb_type: str, operation: str, strength: float, lut_size: int, app_id: Optional[str]):
        """Update configuration from TypeScript."""
        config = lib.CorrectionConfig(
            enabled=enabled,
            cb_type=cb_type,  # type: ignore
            operation=operation,  # type: ignore
            strength=strength,
            lut_size=lut_size
        )
        self._config.update_game_config(config, app_id)
        decky.logger.info(f"Configuration updated for app_id={app_id}")

    async def read_configuration(self, app_id: Optional[str]) -> str:
        """Read configuration and return as dict for TypeScript."""
        config = self._config.get_game_config(app_id)
        # Convert dataclass to dict for JSON serialization
        return json.dumps(asdict(config))

    # async def long_running(self):
    #     await asyncio.sleep(15)
    #     # Passing through a bunch of random data, just as an example
    #     await decky.emit("timer_event", "Hello from the backend!", True, 2)
    #

    async def _main(self):
        self.loop = asyncio.get_event_loop()
        decky.logger.info("Starting colorblind")
        decky.migrate_runtime()
        await self.apply_configuration(None)

    async def _unload(self):
        decky.logger.info("Resetting looks system")
        self.reset_look()
        pass

    async def _uninstall(self):
        decky.logger.info("Resetting looks system")
        self.reset_look()
        pass

    def set_look(self, filename: str):
        decky.logger.info(f"Setting look to {filename}")
        result =  subprocess.run(
            ["/usr/bin/gamescopectl","set_look", filename], env=self._clean_env, text=True, capture_output=True)
        decky.logger.debug(f"set_look exit code {result.returncode}")
        decky.logger.debug(f"set_look stderr {result.stderr}")
        decky.logger.debug(f"set_look stdout {result.stdout}")

    def reset_look(self):
        self.set_look("")





    #
    # # async def start_timer(self):
    # #     self.loop.create_task(self.long_running())
    #
    # # Migrations that should be performed before entering `_main()`.
    # async def _migration(self):
    #     decky.logger.info("Migrating")
    #     # Here's a migration example for logs:
    #     # - `~/.config/decky-template/template.log` will be migrated to `decky.decky_LOG_DIR/template.log`
    #     decky.migrate_logs(os.path.join(decky.DECKY_USER_HOME,
    #                                            ".config", "decky-template", "template.log"))
    #     # Here's a migration example for settings:
    #     # - `~/homebrew/settings/template.json` is migrated to `decky.decky_SETTINGS_DIR/template.json`
    #     # - `~/.config/decky-template/` all files and directories under this root are migrated to `decky.decky_SETTINGS_DIR/`
    #     decky.migrate_settings(
    #         os.path.join(decky.DECKY_HOME, "settings", "template.json"),
    #         os.path.join(decky.DECKY_USER_HOME, ".config", "decky-template"))
    #     # Here's a migration example for runtime data:
    #     # - `~/homebrew/template/` all files and directories under this root are migrated to `decky.decky_RUNTIME_DIR/`
    #     # - `~/.local/share/decky-template/` all files and directories under this root are migrated to `decky.decky_RUNTIME_DIR/`
    #     decky.migrate_runtime(
    #         os.path.join(decky.DECKY_HOME, "template"),
    #         os.path.join(decky.DECKY_USER_HOME, ".local", "share", "decky-template"))

