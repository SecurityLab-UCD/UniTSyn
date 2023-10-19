import pylspclient
import subprocess
import sys
import os
from pylspclient.lsp_structs import (
    Location,
    Position,
    Range,
    TextDocumentIdentifier,
    LANGUAGE_IDENTIFIER,
)
from unitsyncer.util import path2uri, uri2path, ReadPipe
from unitsyncer.source_code import python_get_function_code
from unitsyncer.common import CAPABILITIES
from typing import Optional, Union
from returns.maybe import Maybe, Nothing, Some


def get_lsp_cmd(language: str) -> Optional[list[str]]:
    match language:
        case LANGUAGE_IDENTIFIER.PYTHON:
            return ["python", "-m", "pylsp"]
        case LANGUAGE_IDENTIFIER.C | LANGUAGE_IDENTIFIER.CPP:
            return ["clangd"]
        case LANGUAGE_IDENTIFIER.JAVA:
            return ["jdtls"]
        case _:
            return None


class Synchronizer:
    def __init__(self, workspace_dir: str, language: str) -> None:
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.langID = language
        self.root_uri = path2uri(self.workspace_dir)
        self.workspace_folders = [{"name": "python-lsp", "uri": self.root_uri}]

    def start_lsp_server(self):
        lsp_cmd = get_lsp_cmd(self.langID)
        if lsp_cmd is None:
            sys.stderr.write("Language {language} is not supported\n")
            exit(1)

        self.lsp_proc = subprocess.Popen(
            lsp_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        read_pipe = ReadPipe(self.lsp_proc.stderr)
        read_pipe.start()
        json_rpc_endpoint = pylspclient.JsonRpcEndpoint(
            self.lsp_proc.stdin, self.lsp_proc.stdout
        )
        lsp_endpoint = pylspclient.LspEndpoint(json_rpc_endpoint)
        self.lsp_client = pylspclient.LspClient(lsp_endpoint)

    def initialize(self):
        self.lsp_client.initialize(
            self.lsp_proc.pid,
            self.workspace_dir,
            self.root_uri,
            None,
            CAPABILITIES,
            "off",
            self.workspace_folders,
        )
        self.lsp_client.initialized()

    def open_file(self, file_path: str) -> str:
        """send a file to LSP server

        Args:
            file_path (str): absolute path to the file

        Returns:
            str: uri of the opened file
        """
        uri = path2uri(file_path)
        text = open(file_path, "r").read()
        version = 1
        self.lsp_client.didOpen(
            pylspclient.lsp_structs.TextDocumentItem(uri, self.langID, version, text)
        )
        return uri

    def get_source_of_call(
        self, file_path: str, line: int, col: int
    ) -> Maybe[tuple[str, str | None]]:
        """get the source code of a function called at a specific location in a file

        Args:
            file_path (str): absolute path to file that contains the call
            line (int): line number of the call, 0-indexed
            col (int): column number of the call, 0-indexed

        Returns:
            Maybe[tuple[str, str | None]]: the source code and docstring of the called function
        """
        uri = self.open_file(file_path)

        def_location: Location
        match self.lsp_client.definition(
            TextDocumentIdentifier(uri),
            Position(line, col),
        ):
            case None | []:
                return Nothing
            case [loc, *_]:
                def_location = loc
            case loc:
                if isinstance(loc, Location):
                    def_location = loc
                else:
                    return Nothing
        return python_get_function_code(def_location)

    def stop(self):
        self.lsp_client.shutdown()
        self.lsp_client.exit()
        self.lsp_proc.kill()
