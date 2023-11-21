"""
Finds new repo(s) of the specified language and checks if the repo(s) meet requirements

References

Search query string:
https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax

For path querying specifically:
https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax#path-qualifier
"""
from collections import OrderedDict
import datetime
import fire
import os
import sys

from scripts.check_repo_stats import check_requirements, check_map
from scripts.common import get_graphql_data


def find_repos(language: str, requirements: list[callable], reqs: list[str]) -> int:
    """Searches for new repos based on query parameters and checks if they fit the requirements given while resources are available

    Args:
        search_query (list[str]): queries to narrow down the search
        requirements (list[callable]): List of requirement callables that check if repo meets requirement
        reqs (list[str]): List of values to check against for each callable
            - each req will be called with the callable of the same index in requirements

    Returns:
        int: number of remaining queries
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
    if not os.path.exists(f"./data/repo_cursors/{language.lower()}_cursor.txt"):
        f = open(f"./data/repo_cursors/{language.lower()}_cursor.txt", "x")
        f.close()
    with open(f"./data/repo_cursors/{language.lower()}_cursor.txt", "r") as f:
        try:
            cursor, stars_query, last_stargazerCount, pushed_date = (
                f.read().strip().split("|")
            )
        except ValueError:
            cursor = ""
            stars_query = ">=10"
            last_stargazerCount = ""
            pushed_date = ""

    bulk_size = 100  # How many repos to get at a time
    search_query: str = (
        f"language:{language} stars:{stars_query} archived:false sort:stars"
    )
    if pushed_date:
        search_query += f" pushed:{pushed_date}"
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
    edges = repos["data"]["search"]["edges"]
    for repo in edges:
        repo_data = repo["node"]
        repo_name = f"{repo_data['owner']['login']}/{repo_data['name']}"
        if check_requirements(repo_name, requirements, reqs, repo_data):
            repos_to_save.append(repo_name)

    # Write each repo to a file
    print(f"Writing new repos to ./data/repo_meta/{language}.txt")
    save_repos_to_file(language.lower(), repos_to_save)

    # Save last stargazerCount
    if len(edges) > 0:
        last_stargazerCount = edges[-1]["node"]["stargazerCount"]

    if new_cursor is None:
        new_cursor = ""
        new_pushed_date = None
        if pushed_date:
            # Decrement current pushed_date, keep stars value the same
            date_values = [int(x) for x in pushed_date.split("-")]
            new_pushed_date = datetime.datetime(
                date_values[0], date_values[1], date_values[2]
            ) - datetime.timedelta(days=1)

        if (
            new_pushed_date is None
            or new_pushed_date.date() <= datetime.datetime(2020, 1, 1).date()
        ):
            # New stars value, start from current date
            if new_pushed_date and int(stars_query) == 10:
                # No more search results, just finished checking all repos with 10 stars
                print("No more search results")
                sys.exit(1)

            while True:
                if int(last_stargazerCount) < 10:
                    print("No more search results")
                    sys.exit(1)

                # Check if current stars_query has any repos at all
                search_query: str = f"language:{language} stars:{last_stargazerCount} archived:false sort:stars"
                repos: dict = get_graphql_data(
                    gql_format % (search_query, bulk_size, "")
                )
                if "errors" in repos:
                    sys.exit(f"Fetching repo metadata error: {repos['errors']}")
                elif repos["data"]["search"]["edges"]:
                    break

                last_stargazerCount = str(int(last_stargazerCount) - 1)

            stars_query = last_stargazerCount
            pushed_date = str(datetime.datetime.now().date())
        else:
            # Same stars value, new date
            pushed_date = str(new_pushed_date.date())

    with open(f"./data/repo_cursors/{language.lower()}_cursor.txt", "w") as f:
        # <cursor>|<stars_query>|<pushed_date>
        f.write(f"{new_cursor}|{stars_query}|{last_stargazerCount}|{pushed_date}")

    return int(repos["data"]["rateLimit"]["remaining"])


def save_repos_to_file(language: str, repos_list: list[str]) -> None:
    """Save the repository names to a file named new_<language>.txt in the data/repo_meta directory."""
    file_path = f"./data/repo_meta/{language}.txt"
    # Using "a" to append to the file if it already exists
    with open(file_path, "a") as file:
        for repo_name in repos_list:
            file.write(repo_name + "\n")

    # use OrderedDict to reduce repetition and keep the ordering
    with open(file_path, "r") as file:
        unique_repos = OrderedDict.fromkeys(file.read().splitlines())

    # write back to original txt
    with open(file_path, "w") as file:
        for repo in unique_repos:
            file.write(f"{repo}\n")


# Pass checks_list and reqs with this template: --checks_list='<list>' --reqs='<list>'
# Ex. --reqs='["0", "2020-1-1"]'
# If checking Rust fuzz path, put null in place of where the req should be in the reqs list
def main(
    language: str = "Java",
    checks_list: list[str] = ["stars", "latest commit"],
    reqs: list[str] = ["10", "2020-1-1"],  # Year format should be <year>-<month>-<day>
    num_searches: int = 1,  # How much of the rate limit to use (5000 max)
):
    # Set up requirement callables and reqs
    checks = [check_map[check] for check in checks_list]

    for _ in range(num_searches):
        if find_repos(language, checks, reqs) <= 0:
            print("Rate limit exhausted")
            break


if __name__ == "__main__":
    fire.Fire(main)

