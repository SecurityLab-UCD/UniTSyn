#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-09-27 15:47:58
# @Author  : Jiabo Huang (jiabohuang@tencent.com)

import os
import sys
import ast
import json
import time
import signal
import datetime
import functools
import contextlib
import multiprocessing as mp
from tqdm import tqdm
from typing import Optional, Callable, List, Any


class Timing:
    """providing timing as context or functions"""

    queue: list = []

    def __enter__(self):
        self.tic()
        return self

    def __exit__(self, *args):
        self.tac()

    @staticmethod
    def tic():
        Timing.queue.append(time.time())

    @staticmethod
    def tac():
        assert Timing.queue, "Call Timing.tic before"
        start_at = Timing.queue.pop()
        print(f"Elapsed {datetime.timedelta(seconds=time.time() - start_at)}")


def log_or_skip(path: Optional[str] = None, handler=lambda x: json.dumps(x), **kwargs):
    """log kwargs if path is provided with handler for preprocessing"""
    if not path:
        return
    with open(path, "a") as outfile:
        to_log = kwargs
        if handler:
            to_log = handler(to_log)
        outfile.write(f"{to_log}\n")


def wrap_repo(name: str):
    """wrap repo name from username/repo into username?repo"""
    return "-".join(name.split("/"))


class TimeoutException(Exception):
    pass


@contextlib.contextmanager
def time_limit(seconds: float):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def timestamp(frmt="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.now().strftime(frmt)


def timeout_wrapper(handler: Callable, timeout: int = -1):
    """return None if timeout instead of raising error"""

    def inner(*args, **kwargs):
        if timeout <= 0:
            return handler(*args, **kwargs)
        try:
            with time_limit(timeout):
                return handler(*args, **kwargs)
        except TimeoutException:
            pass
        return None

    return inner


def mp_map_repos(handler: Callable, repo_id_list: List[str], nprocs: int = 0, **kwargs):
    """conduct an unorder map at the level of repo using handler
    make sure handler take a string of repo_id as the first ordered arg
    other args can be passed as named args by kwargs
    """
    results = []
    if nprocs < 1:
        for repo_id in (pbar := tqdm(repo_id_list)):
            pbar.set_description(f"{timestamp()} Processing {repo_id}")
            results.append(handler(repo_id, **kwargs))
    else:
        with mp.Pool(nprocs) as p:
            with tqdm(total=len(repo_id_list)) as pbar:
                for status in p.imap_unordered(
                    functools.partial(handler, **kwargs), repo_id_list
                ):
                    results.append(status)
                    pbar.set_description(timestamp())
                    pbar.update()
    return results
