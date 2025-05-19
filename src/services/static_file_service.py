from io import BufferedReader
import logging
from pathlib import Path
from typing import Dict
import uuid

from flask import Blueprint, Response


class StaticFileService:
    def __init__(self, api_url: str, sub_domain: str):
        self._id_by_file: Dict[str, str] = {}
        self._file_by_id: Dict[str, Path] = {}

        self._api_url = api_url

        if not sub_domain.startswith('/'):
            sub_domain = '/' + sub_domain
        self._sub_domain = sub_domain

    # --- properties ----

    @property
    def blueprint(self) -> Blueprint:
        pb = Blueprint("static_files_bp", __name__, url_prefix=self._sub_domain)

        pb.add_url_rule(
            rule='/<path:id>',
            view_func=self._serve_static_file,
            methods=['GET']
        )
        return pb

    # --- public methods ---

    def get_file_url(self, id: str) -> str:
        """
        Get the URL of a static file.
        :param id: ID of the static file.
        :return: URL of the static file.
        """
        if id not in self._file_by_id:
            raise KeyError(f"Static file '{id}' not found")
        return self._make_url(id)

    def has_file(self, key: str) -> bool:
        """
        Check if a static file is available on the server.
        :param key: Name of the static file.
        :return: True if the file is available, False otherwise.
        """
        return key in self._file_by_id

    def add_file(self, file: Path, id: str = None) -> str:
        """
        Serve a static file from the server.
        :param file_path: Path to the static file.
        :return: path to served file.
        """

        if not file.exists():
            raise FileNotFoundError(f"File {file} not found")

        if file in self._id_by_file:
            return self._id_by_file[file]

        file_size = file.stat().st_size

        if id is None:
            id = uuid.uuid4().hex

        if id in self._file_by_id:
            raise ValueError(f"ID '{id}' already in use")

        self._file_by_id[id] = file
        self._id_by_file[file] = id

        logging.info(f"Serving static file '{file}'({file_size} Bytes) at"
                     f" {self._make_url(id)}")

        return id

    def remove_file(self, id: str) -> None:
        """
        Remove a static file from the server.
        :param file_path: Path to the static file.
        :return: None
        """
        if id in self._file_by_id:
            file = self._file_by_id[id]
            del self._id_by_file[file]
            del self._file_by_id[id]
    # --- private methods ---

    def _get_file(self, key: str) -> BufferedReader:
        if key not in self._file_by_id:
            raise KeyError(f"Static file '{key}' not found")
        return open(self._file_by_id[key], 'rb')

    def _make_url(self, id: str) -> str:
        """
        Create a URL for a static file.
        :param id: ID of the static file.
        :return: URL of the static file.
        """
        return f"http://{self._api_url}{self._sub_domain}/{id}"

    def _serve_static_file(self, id: str):
        """
        Serve a static file from the server.
        :param filename: Name of the static file.
        :return: path to served file.
        """
        if not self.has_file(id):
            return f"Static file '{id}' not found", 404

        file_name = self._file_by_id[id].name

        return Response(
            self._get_file(id).read(),
            mimetype='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{file_name}"',
            }
        )
