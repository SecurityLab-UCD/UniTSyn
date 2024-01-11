"""tests for  get_coverage module in evaluation/execution.py"""
import os
from evaluation.execution import get_coverage
import unittest
import logging
from unitsyncer.common import UNITSYNCER_HOME


class TestEvaluationCoverage(unittest.TestCase):
    """tests for evaluation/execution.py"""

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
        self.assertEqual(get_coverage(focal, test, "python"), 100)

        focal = 'from typing import List\n\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    """ Check if in given list of numbers, are any two numbers closer to each other than\n    given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n    """\n    for idx, elem in enumerate(numbers):\n        for idx2, elem2 in enumerate(numbers):\n            if idx != idx2:\n                distance = abs(elem - elem2)\n                if distance < threshold:\n                    return True\n\n    return False\n'
        test = "\n\nMETADATA = {\n    'author': 'jt',\n    'dataset': 'test'\n}\n\n\ndef check(has_close_elements):\n    assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True\n    assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False\n    assert has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True\n    assert has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) == False\n    assert has_close_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) == True\n    assert has_close_elements([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) == True\n    assert has_close_elements([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) == False\n\ncheck(has_close_elements)"
        self.assertEqual(get_coverage(focal, test, "python"), 100)

    def test_cpp(self):
        focal = "/*\nCheck if in given vector of numbers, are any two numbers closer to each other than\ngiven threshold.\n>>> has_close_elements({1.0, 2.0, 3.0}, 0.5)\nfalse\n>>> has_close_elements({1.0, 2.8, 3.0, 4.0, 5.0, 2.0}, 0.3)\ntrue\n*/\n#include<stdio.h>\n#include<vector>\n#include<math.h>\nusing namespace std;\nbool has_close_elements(vector<float> numbers, float threshold){\n    int i,j;\n    \n    for (i=0;i<numbers.size();i++)\n    for (j=i+1;j<numbers.size();j++)\n    if (abs(numbers[i]-numbers[j])<threshold)\n    return true;\n\n    return false;\n}\n\n"
        test = "#undef NDEBUG\n#include<assert.h>\nint main(){\n    vector<float> a={1.0, 2.0, 3.9, 4.0, 5.0, 2.2};\n    assert (has_close_elements(a, 0.3)==true);\n    assert (has_close_elements(a, 0.05) == false);\n\n    assert (has_close_elements({1.0, 2.0, 5.9, 4.0, 5.0}, 0.95) == true);\n    assert (has_close_elements({1.0, 2.0, 5.9, 4.0, 5.0}, 0.8) ==false);\n    assert (has_close_elements({1.0, 2.0, 3.0, 4.0, 5.0}, 2.0) == true);\n    assert (has_close_elements({1.1, 2.2, 3.1, 4.1, 5.1}, 1.0) == true);\n    assert (has_close_elements({1.1, 2.2, 3.1, 4.1, 5.1}, 0.5) == false);\n    \n}\n"

        self.assertEqual(get_coverage(focal, test, "cpp"), 100)

    def test_java(self):
        java_lib_path = os.path.join(UNITSYNCER_HOME, "evaluation", "lib")

        focal = "import java.util.*;\nimport java.lang.*;\n\nclass Solution {\n    /**\n    Check if in given list of numbers, are any two numbers closer to each other than given threshold.\n    >>> hasCloseElements(Arrays.asList(1.0, 2.0, 3.0), 0.5)\n    false\n    >>> hasCloseElements(Arrays.asList(1.0, 2.8, 3.0, 4.0, 5.0, 2.0), 0.3)\n    true\n     */\n    public boolean hasCloseElements(List<Double> numbers, double threshold) {\n        for (int i = 0; i < numbers.size(); i++) {\n            for (int j = i + 1; j < numbers.size(); j++) {\n                double distance = Math.abs(numbers.get(i) - numbers.get(j));\n                if (distance < threshold) return true;\n            }\n        }\n        return false;\n    }\n}"
        test = "public class Main {\n    public static void main(String[] args) {\n        Solution s = new Solution();\n        List<Boolean> correct = Arrays.asList(\n                s.hasCloseElements(new ArrayList<>(Arrays.asList(11.0, 2.0, 3.9, 4.0, 5.0, 2.2)), 0.3),\n                !s.hasCloseElements(new ArrayList<>(Arrays.asList(1.0, 2.0, 3.9, 4.0, 5.0, 2.2)), 0.05),\n                s.hasCloseElements(new ArrayList<>(Arrays.asList(1.0, 2.0, 5.9, 4.0, 5.0)), 0.95),\n                !s.hasCloseElements(new ArrayList<>(Arrays.asList(1.0, 2.0, 5.9, 4.0, 5.0)), 0.8),\n                s.hasCloseElements(new ArrayList<>(Arrays.asList(1.0, 2.0, 3.0, 4.0, 5.0, 2.0)), 0.1),\n                s.hasCloseElements(new ArrayList<>(Arrays.asList(1.1, 2.2, 3.1, 4.1, 5.1)), 1.0),\n                !s.hasCloseElements(new ArrayList<>(Arrays.asList(1.1, 2.2, 3.1, 4.1, 5.1)), 0.5)\n        );\n        if (correct.contains(false)) {\n            throw new AssertionError();\n        }\n    }\n}"
        self.assertEqual(
            get_coverage(focal, test, "java", java_lib_path=java_lib_path), 100
        )

    def test_js(self):
        focal = """
function add(a, b) {
    switch (a) {
        case 1:
            return 1 + b;
        case 2:
            return 2 + b;
        case 3:
            return 3 + b;
        default:
            break;
    }
    return a + b;
};


"""
        test = """
function test_add() {
    let z= add(1, 2);
    console.log(z);
}
"""
        self.assertEqual(get_coverage(focal, test, "javascript"), 25)

        focal = """
function add(a, b) {
    return a + b;
};
"""
        self.assertEqual(get_coverage(focal, test, "javascript"), 100)

    def test_go(self):
        focal = """
func Add(x int, y int) int {
	return x + y
}
"""
        test = """
func TestAdd(t *testing.T) {
	total := Add(1, 2)
	if total != 3 {
		t.Errorf("add(1, 2) = %d; want 3", total)
	}
}
"""
        self.assertEqual(get_coverage(focal, test, "go"), 100)

        focal = """
func Add(x int, y int) int {
	switch x {
	case 1:
		return 1 + y
	case 2:
		return 2 + y
	case 3:
		return 3 + y
	}
	return x + y
}
"""
        self.assertEqual(get_coverage(focal, test, "go"), 40.0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
