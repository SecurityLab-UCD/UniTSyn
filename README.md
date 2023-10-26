# UniTSyncer

Multilingual **Uni**t **T**est and Function Source **Sync**hronization for CodeLLM

## Requirements

- Python 3.10+
- `requirements.txt`

### Language Server

To run this script on a new project, you need to install the corresponding language server:

| Language   | Language Server                                                                                        | Frontend | Backend  |
| ---------- | ------------------------------------------------------------------------------------------------------ | -------- | -------- |
| Python     | [pylsp](https://github.com/python-lsp/python-lsp-server)                                               | &#x2714; | &#x2714; |
| Java       | [java-language-server](https://github.com/georgewfraser/java-language-server)\*                        | &#x2714; | &#x2714; |
| JavaScript | [typescript-language-server](https://github.com/typescript-language-server/typescript-language-server) | &#x2714; | &#x2714; |
| C/C++      | [clangd](https://clangd.llvm.org/installation.html)                                                    | ToDo     | ToDo     |
| Rust       | [rust-analyzer](https://rust-analyzer.github.io/manual.html)                                           | ToDo     | ToDo     |

\*NOTE: you need git clone the repo to workdir of this project, then follow the instructions in the repo to install the language server.

You can find language server for other languages at
[language-server-protocol/implementors/servers](https://microsoft.github.io/language-server-protocol/implementors/servers/).
Other languages are not supported yet, but will be as the research progresses.
To support a new langauge, you need a frontend to do the following:

1. Collect the unit tests locations and focal functions locations in the repo (see `scripts/collect_test.py` and `scripts/collect_focal.py` for Python frontend).
2. Given a `Location` of function delcaration, extract the function source code (see `unitsyncer/source_code.py`).

## Setup

```bash
mkdir -p data/focal data/repos data/repos_tarball data/tests
source ./scripts/env.sh
cd frontend/parser & python3 build.py
cd ../..
```

## Run

```bash
python3 scripts/download_repos.py
python3 scripts/decompress_repos.py

python3 frontend/<language>/collect_all.py
python3 main.py
```
