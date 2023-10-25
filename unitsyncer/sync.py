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
from unitsyncer.util import path2uri, replace_tabs, uri2path, ReadPipe
from unitsyncer.source_code import get_function_code
from unitsyncer.common import CAPABILITIES, UNITSYNCER_HOME
from typing import Optional, Union
from returns.maybe import Maybe, Nothing, Some
from returns.result import Result, Success, Failure
from returns.converters import maybe_to_result
import logging
from unitsyncer.util import silence


def get_lsp_cmd(language: str) -> Optional[list[str]]:
    match language:
        case LANGUAGE_IDENTIFIER.PYTHON:
            return ["python", "-m", "pylsp"]
        case LANGUAGE_IDENTIFIER.C | LANGUAGE_IDENTIFIER.CPP:
            return ["clangd"]
        case LANGUAGE_IDENTIFIER.JAVA:
            return [
                "bash",
                f"{UNITSYNCER_HOME}/java-language-server/dist/lang_server_linux.sh",
            ]
        case _:
            return None


class Synchronizer:
    def __init__(self, workspace_dir: str, language: str) -> None:
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.langID = language
        self.root_uri = path2uri(self.workspace_dir)
        self.workspace_folders = [{"name": "python-lsp", "uri": self.root_uri}]

    @silence
    def start_lsp_server(self, timeout: int = 10):
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
        lsp_endpoint = pylspclient.LspEndpoint(json_rpc_endpoint, timeout=timeout)
        self.lsp_client = pylspclient.LspClient(lsp_endpoint)

    @silence
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
        text = replace_tabs(open(file_path, "r", errors="replace").read())
        version = 1
        self.lsp_client.didOpen(
            pylspclient.lsp_structs.TextDocumentItem(uri, self.langID, version, text)
        )
        return uri

    def get_source_of_call(
        self, file_path: str, line: int, col: int, verbose: bool = False
    ) -> Result[tuple[str, str | None, str | None], str]:
        """get the source code of a function called at a specific location in a file

        Args:
            file_path (str): absolute path to file that contains the call
            line (int): line number of the call, 0-indexed
            col (int): column number of the call, 0-indexed

        Returns:
            Maybe[tuple[str, str | None]]: the source code and docstring of the called function
        """
        try:
            uri = self.open_file(file_path)
        except Exception as e:
            return Failure(str(e))

        try:
            goto_def = self.lsp_client.definition
            if not verbose:
                goto_def = silence(goto_def)

            response = goto_def(
                TextDocumentIdentifier(uri),
                Position(line, col),
            )
        except Exception as e:
            return Failure(str(e))

        def_location: Location
        match response:
            case None | []:
                return Failure("No definition found")
            case [loc, *_]:
                def_location = loc
            case loc:
                if isinstance(loc, Location):
                    def_location = loc
                else:
                    return Failure(f"Unexpected response from LSP server: {loc}")

        file_path = uri2path(def_location.uri).value_or(str(def_location.uri))

        def not_found_error(_):
            lineno = def_location.range.start.line
            col_offset = def_location.range.start.character
            return f"Source code not found: {file_path}:{lineno}:{col_offset}"

        return (
            maybe_to_result(get_function_code(def_location, self.langID))
            .alt(not_found_error)
            .bind(lambda t: Failure("Empty Source Code") if t[0] == "" else Success(t))
        )

    def stop(self):
        self.lsp_client.shutdown()
        self.lsp_client.exit()
        self.lsp_proc.kill()
