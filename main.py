"""source
https://github.com/yeger00/pylspclient/blob/master/examples/python-language-server.py
"""
import pylspclient
import subprocess
import os
from unitsyncer.util import ReadPipe
from unitsyncer.common import CAPABILITIES


def main():
    pyls_cmd = ["python", "-m", "pylsp"]
    p = subprocess.Popen(
        pyls_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    read_pipe = ReadPipe(p.stderr)
    read_pipe.start()
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(p.stdin, p.stdout)
    # To work with socket: sock_fd = sock.makefile()
    lsp_endpoint = pylspclient.LspEndpoint(json_rpc_endpoint)

    lsp_client = pylspclient.LspClient(lsp_endpoint)
    workspace = os.path.abspath("./repos/py_example")

    root_uri = f"file://{workspace}"
    workspace_folders = [{"name": "python-lsp", "uri": root_uri}]
    print(
        lsp_client.initialize(
            p.pid, workspace, root_uri, None, CAPABILITIES, "off", workspace_folders
        )
    )
    print(lsp_client.initialized())

    # file_path = f"{workspace}/tests/api/api-band-test.c"

    file_path = os.path.join(workspace, "tests/test_add.py")
    uri = "file://" + file_path
    text = open(file_path, "r").read()
    languageId = pylspclient.lsp_structs.LANGUAGE_IDENTIFIER.PYTHON
    version = 1
    lsp_client.didOpen(
        pylspclient.lsp_structs.TextDocumentItem(uri, languageId, version, text)
    )
    try:
        symbols = lsp_client.documentSymbol(
            pylspclient.lsp_structs.TextDocumentIdentifier(uri)
        )
        print("Symbols: ")
        for symbol in symbols:
            print(symbol.name)
    except pylspclient.lsp_structs.ResponseError:
        # documentSymbol is supported from version 8.
        print("Failed to document symbols")

    call = (
        pylspclient.lsp_structs.TextDocumentIdentifier(uri),
        pylspclient.lsp_structs.Position(4, 13),
    )
    def_locs = lsp_client.definition(*call)

    print("===========")
    print(def_locs)
    if len(def_locs) > 0:
        def_loc = def_locs[0]
        print(def_loc.uri)
        print("start ", def_loc.range.start.line, def_loc.range.start.character)
        print("end ", def_loc.range.end.line, def_loc.range.end.character)
    print("===========")

    lsp_client.shutdown()
    lsp_client.exit()


if __name__ == "__main__":
    main()
