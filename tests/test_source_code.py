import unittest
import os
import logging
from unitsyncer.source_code import python_get_function_code
from returns.maybe import Nothing, Some
from pylspclient.lsp_structs import Location, Position, Range


class TestSourceCode(unittest.TestCase):
    def test_python_get_function_code(self):
        uri = f"file://{os.getcwd()}/repos/py_example/src/add.py"
        range_ = Range(Position(0, 4), Position(0, 7))
        loc = Location(uri, range_)
        add_src = "\n\ndef add(x: int, y: int) -> int:\n    return (x + y)\n"

        self.assertEqual(python_get_function_code(loc), Some(add_src))

    def test_python_get_function_code_not_found(self):
        uri = f"file://{os.getcwd()}/repos/py_example/src/add.py"
        range_ = Range(Position(1, 4), Position(1, 7))
        loc = Location(uri, range_)

        self.assertEqual(python_get_function_code(loc), Nothing)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
