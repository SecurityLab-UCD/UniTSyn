"""
Point of this script is only to check if a repo fulfills certain requirements

Use another script to automate getting repos


References

Parts 1 and 2 of a medium blog explaining the query:
https://fabiomolinar.medium.com/using-githubs-graphql-to-retrieve-a-list-of-repositories-their-commits-and-some-other-stuff-ccbbb4e96d78
https://fabiomolinar.medium.com/using-githubs-graphql-to-retrieve-a-list-of-repositories-their-commits-and-some-other-stuff-ce2f73432f7

Github Ranking Repo:
https://github.com/EvanLi/Github-Ranking/blob/master/source/

Repository Object:
https://docs.github.com/en/graphql/reference/objects#repository

"""
import json
from datetime import datetime

from common import get_graphql_data


def req_enough_stars(metadata: dict) -> bool:
    """Checks if Github repository has enough stars"""
    if metadata["stargazerCount"] >= 10:
        return True
    return False


def req_latest_commit(metadata: dict) -> bool:
    """Checks if Github repository has a valid latest commit"""
    latest_commit_date = datetime.fromisoformat(metadata["pushedAt"]).date()
    req_date = datetime.date(2020, 1, 1)
    if req_date > latest_commit_date:
        return True
    return False


def check_requirements(repo: str, requirements: list[callable]) -> bool:
    """Checks if Github repository meets requirements

    Args:
        repo (str): Github repository in repo_owner/repo_name format
        requirements (list[callable]): List of requirement callables that check if repo meets requirement

    Returns:
        bool: True if repo meets requirements, False otherwise
    """

    repo_query = repo.split("/")

    # Get repo data
    # Query will return the language, last commit, and number of stars of repo
    gql_format = """
    query {
        rateLimit {
            cost
            remaining
            resetAt
        }
        repository(name:"%s", owner:"%s"){
            primaryLanguage {
                name
            }
            pushedAt
            stargazerCount
        }
    }
    """
    metadata = json.loads(get_graphql_data(gql_format % (repo_query[0], repo_query[1])))

    # Check requirements
    for r in requirements:
        if not r(metadata):
            return False
    return True

