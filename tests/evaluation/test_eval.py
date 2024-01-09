"""tests for rust coverage module"""
import json
import os
from evaluation.execution import get_coverage
import unittest
import logging


class TestEvaluationCoverage(unittest.TestCase):
    def test_python(self):
        focal = """
def add(x: int, y: int) -> int:
    match x:
        case 1:
            return 1 + y
        case 2:
            return 2 + y
        case 3:
            return 3 + y
        case _:
            return x + y
        """
        test = """
def test_add():
    assert add(1, 2) == 3
        """
        self.assertEqual(get_coverage(focal, test, "python"), 31.25)

        focal = """
def add(x: int, y: int) -> int:
    return x + y
        """
        test = """
def test_add():
    assert add(1, 2) == 3
        """
        self.assertEqual(get_coverage(focal, test, "python"), 100)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
