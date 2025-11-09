import json
import os
import subprocess
import time
from typing import Optional, Generic, TypeVar
import decky
import asyncio
import colorblind_plugin as lib
from dataclasses import asdict, dataclass

from colorblind_plugin import CorrectionConfig
from colorblind_plugin.plugin_config import ColorBlindSettings


def _get_clean_env():
    """Get environment with cleared LD_LIBRARY_PATH to fix decky-loader subprocess issues"""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = ""
    # XDG_RUNTIME_DIR must be set otherwise gamescopectl won't be able to detect the display
    env["XDG_RUNTIME_DIR"] = "/run/user/1000"

    return env

ResultType = TypeVar('ResultType')


@dataclass
class Result(Generic[ResultType]):
    result: Optional[ResultType]
    err: Optional[str]
    ok: bool

    @staticmethod
    def ok(result: ResultType):
        return Result(ok=True, err=None, result=result)

    @staticmethod
    def err(err: str):
        return Result(ok=False, err=err, result=None)


class Plugin:
    _config = ColorBlindSettings()
    _clean_env = _get_clean_env()

    async def apply_configuration(self, app_id: Optional[str]) -> dict:
        """Apply the current configuration by generating and setting LUT."""
        correction_config = self._config.get_game_config(app_id)

        if not correction_config.enabled:
            decky.logger.info("Correction disabled, skipping LUT application")
            self.reset_look()
            return asdict(Result.ok(None))

        lut_path = os.path.join(decky.DECKY_PLUGIN_RUNTIME_DIR, "lut.cube")
        decky.logger.info(f"Generating LUT: {correction_config.cb_type}, {correction_config.operation}, strength={correction_config.strength}")

        start_time = time.time()
        lib.lut_generator.generate_lut(
            cb_type=correction_config.cb_type,
            operation=correction_config.operation,
            strength=correction_config.strength,
            output_path=lut_path,
            lut_size=correction_config.lut_size
        )
        end_time = time.time()
        elapsed = (end_time - start_time) * 1000
        decky.logger.info(f"LUT generation took {elapsed:.2f}ms")

        result = self.set_look(lut_path)
        if not result.ok:
            decky.logger.info(f"Failed to apply LUT: {result.err}")
        else:
            decky.logger.info(f"LUT applied successfully")
        return asdict(result)

    async def update_configuration(self, config: dict, app_id: Optional[str]) -> dict:
        """Update configuration from TypeScript."""
        decky.logger.info(f"Updating configuration for app_id={app_id}, config={config}")
        config = CorrectionConfig(**config)
        self._config.update_game_config(config, app_id)
        decky.logger.info(f"Configuration updated for app_id={app_id}")
        return asdict(Result.ok(None))

    async def read_configuration(self, app_id: Optional[str]) -> dict:
        """Read configuration and return as dict for TypeScript."""
        config = self._config.get_game_config(app_id)
        # Convert dataclass to dict for JSON serialization
        return asdict(Result.ok(config))

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

    def set_look(self, filename: str) -> Result[None]:
        decky.logger.info(f"Setting look to {filename}")
        result =  subprocess.run(
            ["/usr/bin/gamescopectl","set_look", filename], env=self._clean_env, text=True, capture_output=True)
        decky.logger.debug(f"set_look exit code {result.returncode}")
        decky.logger.debug(f"set_look stderr {result.stderr}")
        decky.logger.debug(f"set_look stdout {result.stdout}")
        if result.returncode != 0:
            return Result.err(f"set_look failed: returncode={result.returncode} stderr={result.stderr}")
        return Result.ok(None)

    def reset_look(self):
        self.set_look("")

