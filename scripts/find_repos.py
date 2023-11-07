"""
Finds new repo(s) of the specified language and checks if the repo(s) meet requirements

References

Search query string:
https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax

For path querying specifically:
https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax#path-qualifier
"""
import fire
import os
import sys

import check_repo_stats
from common import get_graphql_data

def find_repos(language: str, requirements: list[callable], reqs: list[str]) -> None:
    """Searches for new repos based on query parameters and checks if they fit the requirements given while resources are available

    Args:
        search_query (list[str]): queries to narrow down the search
        requirements (list[callable]): List of requirement callables that check if repo meets requirement
        reqs (list[str]): List of values to check against for each callable
            - each req will be called with the callable of the same index in requirements
    """

    gql_format = """
    query {
        rateLimit{
            cost
            remaining
            resetAt
        }
        search(query: "%s", type: REPOSITORY, first:%d %s) {
            repositoryCount
            pageInfo { endCursor }
            edges {
                node {
                    ...on Repository {
                        id
                        owner {
                            login
                        }
                        name
                        url
                        isArchived
                        primaryLanguage {
                            name
                        }
                        pushedAt
                        stargazerCount
                        object(expression: "HEAD:") {
                            ... on Tree {
                                entries {
                                    name
                                    type
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    # Read in last used cursor
    # Cursor can specify where to start looking in search results, save to a file to know where to start searching next time
    if not os.path.exists(f"{language.lower()}_cursor.txt"):
        f = open(f"{language.lower()}_cursor.txt", "x")
        f.close()
    with open(f"{language.lower()}_cursor.txt", "r") as f:
        cursor = f.read().strip()

    bulk_size = 100  # How many repos to get at a time
    stars = 10  # Assuming stars is always a requirement to refine search results
    search_query: str = f"language:{language} stars:>={stars} sort:stars"
    # Set cursor if it exists
    if cursor != "":
        cursor = f', after:"{cursor}"'

    repos: dict = get_graphql_data(gql_format % (search_query, bulk_size, cursor))
    if "errors" in repos:
        sys.exit(f"Fetching repo metadata error: {repos['errors']}")

    print(f'{repos["data"]["rateLimit"]}\n')

    new_cursor = repos["data"]["search"]["pageInfo"]["endCursor"]

    # Check repos
    repos_to_save = []
    for repo in repos["data"]["search"]["edges"]:
        repo_data = repo["node"]
        repo_name = f"{repo_data['owner']['login']}/{repo_data['name']}"
        if check_repo_stats.check_requirements(
            repo_name, requirements, reqs, repo_data
        ):
            repos_to_save.append(repo_name)

    # Write each repo to a file
    save_repos_to_file(language.lower(), repos_to_save)

    # Update the cursor for the next execution
    with open(f"{language.lower()}_cursor.txt", "w") as f:
        f.write(new_cursor)


def save_repos_to_file(language: str, repos_list: list[str]) -> None:
    """Save the repository names to a file named new_<language>.txt in the ../data/repo_meta directory."""
    file_path = f"./data/repo_meta/new_{language}.txt"
    # Using "a" to append to the file if it already exists
    with open(file_path, "a") as file:
        for repo_name in repos_list:
            file.write(repo_name + "\n")


# Pass checks_list and reqs with this template: --checks_list='<list>' --reqs='<list>'
# Ex. --reqs='["0", "2020-1-1"]'
# If checking Rust fuzz path, put null in place of where the req should be in the reqs list
def main(
    language: str = "Java",
    checks_list: list[str] = ["stars", "latest commit"],
    reqs: list[str] = ["10", "2020-1-1"],  # Year format should be <year>-<month>-<day>
):
    # Set up requirement callables and reqs
    check_map = {
        "stars": check_repo_stats.req_enough_stars,
        "latest commit": check_repo_stats.req_latest_commit,
        "language": check_repo_stats.req_language,
        "fuzzers": check_repo_stats.req_fuzzers,
    }
    checks = [check_map[check] for check in checks_list]

    find_repos(language, checks, reqs)


if __name__ == "__main__":
    fire.Fire(main)

