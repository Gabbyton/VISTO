import importlib.resources as pkg_resources
from configparser import ConfigParser
from pathlib import Path


class VisualizerRef:

    def __init__(self):
        self._read_config()

    def _read_config(self):
        config = ConfigParser()

        current_file_folder = Path(__file__)
        # retrieve configuration file from the grandparent directory
        config_path = current_file_folder.parent.parent / "config.ini"

        if config_path.exists():
            config.read(config_path)
        else:
            with pkg_resources.open_text("visto", "config.ini") as config_file:
                config.read_file(config_file)

        self._config = config

    def get_file_source_path(self):
        config = self._get_config()
        return config["file_params"]["file_source_path"]

    def get_triple_output_path(self):
        config = self._get_config()
        return config["file_params"]["triple_output_path"]

    def get_temp_path(self):
        config = self._get_config()
        return config["file_params"]["temp_path"]

    def _get_config(self):
        return self._config
