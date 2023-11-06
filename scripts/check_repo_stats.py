"""
This script checks if a repo fulfills certain requirements
Can customize what requirements to check and values to check against


References

Parts 1 and 2 of a medium blog explaining the query:
https://fabiomolinar.medium.com/using-githubs-graphql-to-retrieve-a-list-of-repositories-their-commits-and-some-other-stuff-ccbbb4e96d78
https://fabiomolinar.medium.com/using-githubs-graphql-to-retrieve-a-list-of-repositories-their-commits-and-some-other-stuff-ce2f73432f7

Repository Object:
https://docs.github.com/en/graphql/reference/objects#repository

"""
from datetime import datetime
import fire
import sys

from common import get_graphql_data


#### Requirement Callables ####
def req_enough_stars(metadata: dict, req_stars: str = "10") -> bool:
    """Checks if Github repository has enough stars"""
    return metadata["stargazerCount"] >= int(req_stars)


def req_latest_commit(metadata: dict, date_str: str = "2020-1-1") -> bool:
    """Checks if Github repository has a valid latest commit"""
    # latest_commit_date = datetime.fromisoformat(metadata["pushedAt"])
    date_values = metadata["pushedAt"].split("T")[0].split("-")
    latest_commit_date = datetime(
        int(date_values[0]), int(date_values[1]), int(date_values[2])
    )
    date = date_str.split("-")
    req_date = datetime(int(date[0]), int(date[1]), int(date[2]))
    return latest_commit_date.date() > req_date.date()


def req_language(metadata: dict, language: str = "java") -> bool:
    """Checks if Github repository has correct language"""
    return metadata["primaryLanguage"]["name"].lower() == language.lower()


def req_fuzzers(metadata: dict) -> bool:
    """ "Checks if Github repository of Rust has fuzz file"""
    contents = metadata["object"]["entries"]
    for item in contents:
        if item["name"] == "fuzz" and item["type"] == "tree":
            return True
    return False


#### End Requirement Callables ####


def check_requirements(
    repo: str, requirements: list[callable], reqs: list[str]
) -> bool:
    """Checks if Github repository meets requirements

    Args:
        repo (str): Github repository in repo_owner/repo_name format
        requirements (list[callable]): List of requirement callables that check if repo meets requirement
        reqs (list[str]): List of values to check against for each callable
            - each req will be called with the callable of the same index in requirements

    Returns:
        bool: True if repo meets requirements, False otherwise
    """

    repo_query = repo.split("/")

    # Get repo data
    gql_format = """
    query {
        rateLimit {
            cost
            remaining
            resetAt
        }
        repository(name:"%s", owner:"%s"){
            id
            owner {
                login
            }
            name
            url
            archivedAt
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
    """
    # Example of format of metadata:
    # {
    #   'data': {
    #       'rateLimit': {'cost': <cost>, 'remaining': <remaining>, 'resetAt': <ISO-8601 datetime>},
    #       'repository': {'primaryLanguage': <language>, 'pushedAt': <ISO-8601 datetime>, 'stargazerCount': <num_stars>}
    #   }
    # }
    metadata: dict = get_graphql_data(gql_format % (repo_query[1], repo_query[0]))
    if "errors" in metadata:
        sys.exit(f"Fetching repo metadata error: {metadata['errors']}")

    print(f"{repo} metadata: {metadata}")

    # If repo is archived, automatic fail
    if metadata["data"]["repository"]["archivedAt"] is not None:
        print("Repo is archived")
        return False

    # Check requirements
    for i in range(len(requirements)):
        if requirements[i] == req_fuzzers and not requirements[i](
            metadata["data"]["repository"]
        ):
            print(f"Error with req {requirements[i].__name__}")
            return False
        elif not requirements[i](metadata["data"]["repository"], reqs[i]):
            print(f"Error with req {requirements[i].__name__} with requirement {reqs[i]}")
            return False
    return True


# Pass checks_list and reqs with this template: --checks_list='<list>' --reqs='<list>'
# Ex. --reqs='["0", "2020-1-1"]'
# If checking Rust fuzz path, put null in place of where the req should be in the reqs list
def main(
    repo_id_list: str = "ethanbwang/test",
    checks_list: list[str] = ["stars", "latest commit"],
    reqs: list[str] = ["10", "2020-1-1"],  # Year format should be <year>-<month>-<day>
):
    # if repo_id_list is a file then load lines
    # otherwise it is the id of a specific repo
    try:
        repo_id_list = [l.strip() for l in open(repo_id_list, "r").readlines()]
    except:
        repo_id_list = [repo_id_list]

    # Map elements of checks_list to callables
    check_map = {
        "stars": req_enough_stars,
        "latest commit": req_latest_commit,
        "language": req_language,
        "fuzzers": req_fuzzers,
    }
    checks = [check_map[check] for check in checks_list]

    for repo in repo_id_list:
        if check_requirements(repo, checks, reqs):
            print(f"{repo} meets the requirements\n")
        else:
            print(f"{repo} does not meet the requirements\n")


if __name__ == "__main__":
    fire.Fire(main)

