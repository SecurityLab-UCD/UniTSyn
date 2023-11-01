import json
import requests
import time


def get_graphql_data(GQL):
    """
    use graphql to get data
    """
    access_token = get_access_token()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Authorization": "bearer {}".format(access_token),
    }
    s = requests.session()
    s.keep_alive = False  # don't keep the session
    graphql_api = "https://api.github.com/graphql"
    for _ in range(5):
        time.sleep(2)  # not get so fast
        try:
            # requests.packages.urllib3.disable_warnings() # disable InsecureRequestWarning of verify=False,
            r = requests.post(
                url=graphql_api, json={"query": GQL}, headers=headers, timeout=30
            )
            if r.status_code != 200:
                print(
                    f"Can not retrieve from {GQL}. Response status is {r.status_code}, content is {r.content}."
                )
            else:
                return r.json()
        except Exception as e:
            print(e)
            time.sleep(5)

