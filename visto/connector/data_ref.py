import os
from os import path
from pathlib import Path


class DataRef:

    def __init__(self):
        self._ontology_paths = None

        current_file_folder = Path(__file__)
        # retrieve the ontology path from the grandparent folder
        self._ontology_folder_path = current_file_folder.parent.parent / "ontologies"
        self._set_ontology_paths()

    def _set_ontology_paths(self):
        ontology_paths = dict()
        for root, _, files in os.walk(self._get_ontology_folder_path()):
            for file in files:
                file_name = file.split(".")[0]
                file_path = path.join(root, file)
                ontology_paths[file_name] = file_path

        self._ontology_paths = ontology_paths

    def get_ontology_path(self, name):
        return self._ontology_paths[name]

    def _get_ontology_folder_path(self):
        return self._ontology_folder_path
