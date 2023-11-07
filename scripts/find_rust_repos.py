"""
Finds new Rust repo(s) and checks if the repo(s) meet requirements

"""
import sys
from check_repo_stats import check_requirements
from common import get_graphql_data

def find_rust_repos(requirements: list[callable], reqs: list[str]) -> None:
    # Read in last used cursor
    with open(f"{language}_cursor.txt", "r") as f:
        cursor = f.read().strip()

    # Cursor can specify where to start looking, save to a file to know where to start searching next time?
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
                        primaryLanguage {
                            name
                        }
                        stargazers {
                            totalCount
                        }
                        pushedAt
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

    bulk_size = 50
    # Can maybe specify the requirements in the search query
    # Doesn't look like latest commit can be specified in the search query
    language = '"Rust"'  # Surround language with double quotes for exact search
    stars = 10

    search_query: str = f"language:{language} stars:>{stars} sort:stars"
    repos: dict = get_graphql_data(gql_format % (search_query, bulk_size, "%s"))
    if "errors" in repos:
        sys.exit(f"Fetching repo metadata error: {repos['errors']}")

    new_cursor = repos["data"]["search"]["pageInfo"]["endCursor"]

    # Check repos
    repos_to_save = []
    for repo in repos["data"]["search"]["edges"]:
        repo_name = f"{repo['owner']['login']}/{repo['name']}"
        if check_requirements(repo_name, requirements, reqs):
            print(f"Repository {repo_name} meets the requirements.")
            repos_to_save.append(repo_name)

    # Write each repo to a file
    save_repos_to_file(language.strip('"'), repos_to_save)  # Remove double quotes from the language string if present

    # Update the cursor for the next execution
    with open(f"{language.strip('"')}_cursor.txt", "w") as f:
        f.write(new_cursor)   


# define requirements and reqs list
requirements = [req_enough_stars, req_latest_commit, req_language, req_fuzzers]
reqs = ['10', '2021-01-01', 'Rust', None]  # reqs that satisfied with rust


def save_repos_to_file(language: str, repos_list: list[str]) -> None:
    """Save the repository names to a file named <language>.txt in the ../data/repo_meta directory."""
    file_path = f"../data/repo_meta/{language}.txt"
    with open(file_path, "a") as file:  # Using "a" to append to the file if it already exists
        for repo_name in repos_list:
            file.write(repo_name + "\n")

if __name__ == "__main__":
    find_rust_repos(requirements, reqs)
