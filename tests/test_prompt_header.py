"""tests for get_def_header module in evaluation/extract_def.py"""
import os
from unitsyncer.extract_def import get_def_header
import unittest
import logging
from unitsyncer.common import UNITSYNCER_HOME


class TestGetDefHeader(unittest.TestCase):
    def test_py(self):
        test = "\n\nMETADATA = {\n    'author': 'jt',\n    'dataset': 'test'\n}\n\n\ndef check(has_close_elements):\n    assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True\n    assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False\n    assert has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True\n    assert has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) == False\n    assert has_close_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) == True\n    assert has_close_elements([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) == True\n    assert has_close_elements([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) == False\n\ncheck(has_close_elements)"

        self.assertEqual(
            get_def_header(test, "python"), "def check(has_close_elements):\n"
        )

    def test_go(self):
        test = "func TestHasCloseElements(t *testing.T) {\n    assert := assert.New(t)\n    assert.Equal(true, HasCloseElements([]float64{11.0, 2.0, 3.9, 4.0, 5.0, 2.2}, 0.3))\n    assert.Equal(false, HasCloseElements([]float64{1.0, 2.0, 3.9, 4.0, 5.0, 2.2}, 0.05))\n    assert.Equal(true, HasCloseElements([]float64{1.0, 2.0, 5.9, 4.0, 5.0}, 0.95))\n    assert.Equal(false, HasCloseElements([]float64{1.0, 2.0, 5.9, 4.0, 5.0}, 0.8))\n    assert.Equal(true, HasCloseElements([]float64{1.0, 2.0, 3.0, 4.0, 5.0, 2.0}, 0.1))\n    assert.Equal(true, HasCloseElements([]float64{1.1, 2.2, 3.1, 4.1, 5.1}, 1.0))\n    assert.Equal(false, HasCloseElements([]float64{1.1, 2.2, 3.1, 4.1, 5.1}, 0.5))\n}\n"
        self.assertEqual(
            get_def_header(test, "go"),
            "func TestHasCloseElements(t *testing.T) {\n    assert := assert.New(t)\n",
        )

    def test_js(self):
        test = "const testHasCloseElements = () => {\n  console.assert(hasCloseElements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) === true)\n  console.assert(\n    hasCloseElements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) === false\n  )\n  console.assert(hasCloseElements([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) === true)\n  console.assert(hasCloseElements([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) === false)\n  console.assert(hasCloseElements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) === true)\n  console.assert(hasCloseElements([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) === true)\n  console.assert(hasCloseElements([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) === false)\n}\n\ntestHasCloseElements()\n"

        self.assertEqual(
            get_def_header(test, "js"),
            "const testHasCloseElements = () => {\n",
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
