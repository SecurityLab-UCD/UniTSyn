# Test collection

To collect manual tests (testing function) from the github repos used in CodeSearchNet

## Scripts

- `data/`: default directory for storing generated content
- `colect_focal.py`: to collect the potential focal functions from repos
- `collect_test.py`: to collect all the testing functions from repos
- `decompress_repos.py`: to decompress the downloaded repos' tarball
- `download_repos.py`: to download repos by their "username/repo"
- `navigate.py`: provide util functions for ast navigation
- `utils.py`: other util functions

## Pipeline:

### 1. download repos from Github

The lists of repos composed by different programming languages are provided in `data/repo_meta/`.
There are six files corresponding to go, java, javascript, php, python and ruby.
Use `download_repo.py` to download a single or a list of repos to local.
Available options are

- `--repo_id_list`: can be a single repo name or a list of repo
- `fetch_timeout`: maximal time in seconds for fetching the information about a repo
- `download_timeout`: maximal time in seconds for downloading a repo
- `oroot`: root directory for storing downloaded repos
- `limits`: if a list of repos is provided, use `--limits K` to download the first `K` repos in the list only
- `decompress`: whether to decompress the downloaded tarball

### 2. decompress the downloaded repos' tarball (Optional)

if repos are downloaded without decompression, use `decompress_repos.py` to do this with multiprocessing.
Available options are:

- `repo_id_list`: see `download_repo.py`
- `timeout`: maximal time in seconds for decompressing a repo
- `iroot`: directory to load tarball
- `oroot`: directory to save the decompressed repos

### 3. collect tests from repos

Once repos are downloaded and decompressed, use `collect_test.py` to collect all the tests from a repo or a list of repos.
Available options are:

- `repo_id_list`: see `download_repo.py`
- `repo_root`: directory to load repo
- `test_root`: directory to save the collected tests
- `timeout`: maximal time in seconds for parsing tests from a repo
- `nprocs`: number of processes for multiprocessing
- `limits`: see `decompress_repos.py`

The `collect_test.py` will generate a list of `.txt` files with each file corresponding to a repo.
Each line in a generated file is the id of a testing function in that repo.
The id of function is constructed as
`<py_module_path>::<parent_class_0>::...::<parent_class_i>::<function>` so that we can precisely locate every function by its id.

### 4. collect the name of the potential focal function in each test

Given the discovered tests, use `collect_focal.py` to mine the potential focal function's name for each.
Available options are:

- `repo_id_list`: see `download_repo.py`
- `test_root`: directory to load tests
- `repo_root`: directory to load repos
- `focal_root`: directory to save the discovered focal functions
- `timeout`: maximal time in seconds for parsing focal functions in a repo
- `nprocs`: see `collect_test.py`
- `limits`: see `decompress_repos.py`

The `collect_focal.py` will generate a list of `.jsonl` files corresponding to the provided repos. Each line in a generated file is a dictionary with two keys `{test: <test_id>, focal: <focal_id>}`

### 5. collect the source code of focal functions

Once we got the id of all test-focal pairs, use `collect_source.py` to collect their source code.
Available options are:

- `repo_id_list`: see `download_repo.py`
- `repo_root`: directory to load repos
- `focal_root`: path to load id of test-focal pairs
- `source_path`: path to save the collected source code of test-focal pairs
- `timeout`: maximal time in seconds for collecting source code
- `nprocs`: see `collect_test.py`
- `limits`: see `decompress_repos.py`

The `collect_source.py` will generate a SINGLE `.jsonl` file for all the repos, each line of it is a dictionary:

```
{
    'test_id': <test_id>,
    'test': <test_source_code>,
    'code_id': <focal_id>,
    'code': <focal_source_code>,
    'docstring': <docstr_parsed_from_focal_source_code>
}
```

And that's the final results we need for LLM training.

Please feel free to let me know if there is anything unclear or any bugs.
