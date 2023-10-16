CAPABILITIES = {
    "textDocument": {
        "codeAction": {"dynamicRegistration": True},
        "codeLens": {"dynamicRegistration": True},
        "colorProvider": {"dynamicRegistration": True},
        "completion": {
            "completionItem": {
                "commitCharactersSupport": True,
                "documentationFormat": ["markdown", "plaintext"],
                "snippetSupport": True,
            },
            "completionItemKind": {
                "valueSet": [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                ]
            },
            "contextSupport": True,
            "dynamicRegistration": True,
        },
        "definition": {"dynamicRegistration": True},
        "documentHighlight": {"dynamicRegistration": True},
        "documentLink": {"dynamicRegistration": True},
        "documentSymbol": {
            "dynamicRegistration": True,
            "symbolKind": {
                "valueSet": [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                ]
            },
        },
        "formatting": {"dynamicRegistration": True},
        "hover": {
            "contentFormat": ["markdown", "plaintext"],
            "dynamicRegistration": True,
        },
        "implementation": {"dynamicRegistration": True},
        "onTypeFormatting": {"dynamicRegistration": True},
        "publishDiagnostics": {"relatedInformation": True},
        "rangeFormatting": {"dynamicRegistration": True},
        "references": {"dynamicRegistration": True},
        "rename": {"dynamicRegistration": True},
        "signatureHelp": {
            "dynamicRegistration": True,
            "signatureInformation": {"documentationFormat": ["markdown", "plaintext"]},
        },
        "synchronization": {
            "didSave": True,
            "dynamicRegistration": True,
            "willSave": True,
            "willSaveWaitUntil": True,
        },
        "typeDefinition": {"dynamicRegistration": True},
    },
    "workspace": {
        "applyEdit": True,
        "configuration": True,
        "didChangeConfiguration": {"dynamicRegistration": True},
        "didChangeWatchedFiles": {"dynamicRegistration": True},
        "executeCommand": {"dynamicRegistration": True},
        "symbol": {
            "dynamicRegistration": True,
            "symbolKind": {
                "valueSet": [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                ]
            },
        },
        "workspaceEdit": {"documentChanges": True},
        "workspaceFolders": True,
    },
}
