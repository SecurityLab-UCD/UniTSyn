"""tests for rust coverage module"""
import json
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

    def test_cpp(self):
        focal = """
int add(int x, int y) {
    switch(x){
        case 1:
            return 1 + y;
        case 2:
            return 2 + y;
        case 3:
            return 3 + y;
        default:
            return x + y;
    }
}
"""
        test = """
int test_add() {
  int z = add(1, 2);
  if (z == 3)
    return 0;

  return 1;
}
"""
        # 31.25
        self.assertEqual(get_coverage(focal, test, "cpp"), 50)

        focal = """
int add(int x, int y) { return x + y; }
"""
        self.assertEqual(get_coverage(focal, test, "cpp"), 100)

    def test_java(self):
        java_lib_path = os.path.join(UNITSYNCER_HOME, "evaluation", "lib")
        focal = """
public static int add(int x, int y) {
    if (x > 10) {
        return x + y + 1;
    } else {
        return x + y;
    }
}
"""
        test = """
public static void test_add() {
    int z = add(1, 2);
}
"""
        self.assertEqual(
            get_coverage(focal, test, "java", java_lib_path=java_lib_path), 50
        )

        focal = """
public static int add(int x, int y) {
    return x + y;
}
"""
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
