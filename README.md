# UniTSyncer

Multilingual **Uni**t **T**est and Function Source **Sync**hronization for CodeLLM

## Requirements

- Python 3.10+
- `requirements.txt`

### Language Server

To run this script on a new project, you need to install the corresponding language server:

| Language | Language Server                                              | Frontend | Backend  |
| -------- | ------------------------------------------------------------ | -------- | -------- |
| Python   | [pylsp](https://github.com/python-lsp/python-lsp-server)     | &#x2714; | &#x2714; |
| C/C++    | [clangd](https://clangd.llvm.org/installation.html)          | ToDo     | &#x2714; |
| Rust     | [rust-analyzer](https://rust-analyzer.github.io/manual.html) | ToDo     | ToDo     |

Other languages are not supported yet, but will be as the research progresses.
To support a new langauge, you need a frontend to do the following:
1. Collect the unit tests locations and focal functions locations in the repo (see `scripts/collect_test.py` and `scripts/collect_focal.py` for Python frontend).
2. Given a `Location` of function delcaration, extract the function source code (see `unitsyncer/source_code.py`).

## Run

```bash
mkdir -p data/focal data/repos data/repos_tarball data/tests
python3 scripts/download_repos.py
python3 scripts/decompress_repos.py
python3 scripts/collect_test.py
python3 scripts/collect_focal.py

python3 main.py
```
