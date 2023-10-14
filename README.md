# UniTSyncer

Multilingual **Uni**t **T**est and Function Source **Sync**hronization for CodeLLM

## Requirements

- Python 3.10+
- `requirements.txt`

### Language Server

To run this script on a new project, you need to install the corresponding language server:

| Language | Language Server                                              | Supported |
| -------- | ------------------------------------------------------------ | --------- |
| Python   | [pylsp](https://github.com/python-lsp/python-lsp-server)     | &#x2714;  |
| C/C++    | [clangd](https://clangd.llvm.org/installation.html)          | &#x2714;  |
| Rust     | [rust-analyzer](https://rust-analyzer.github.io/manual.html) | ToDo      |

Other languages are not supported yet, but will be as the research progresses.

## Run

```bash
mkdir -p data/focal data/repos data/repos_tarball data/tests
python3 scripts/download_repos.py
python3 scripts/decompress_repos.py
python3 scripts/collect_test.py
python3 scripts/collect_focal.py

python3 main.py
```
