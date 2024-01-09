"""Execution Runtime Metrics for Python, Java, Go, C++, and JS"""
import fire
import json
import docker
import contextlib
import os
import tempfile
import subprocess


@contextlib.contextmanager
def build_image(repo_id: str):
    _, workdir = repo_id.split("/")
    dockerfile = f"""
FROM yfhe0602/unitsyncer-eval:python
ENV DEBIAN_FRONTEND noninteractive
RUN git clone https://github.com/{repo_id}
WORKDIR {workdir}
RUN pip install -r requirements.txt
"""
    temp_file = tempfile.NamedTemporaryFile(prefix="unitsyncer_")
    with open(temp_file.name, "w") as f:
        f.write(dockerfile)
    try:
        subprocess.run(
            ["docker", "build", "--tag", repo_id, ".", "-f", temp_file.name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        yield
    finally:
        subprocess.run(
            ["docker", "rmi", repo_id, "-f"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main():
    repo_id = "slarse/clanimtk"
    with build_image(repo_id):
        client = docker.from_env()
        res = client.containers.run(repo_id, "pytest --cov=. tests")
        print(res)


if __name__ == "__main__":
    fire.Fire(main)
