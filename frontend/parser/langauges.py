from tree_sitter import Language, Parser, Tree
from unitsyncer.common import UNITSYNCER_HOME


JAVA_LANGUAGE = Language(f"{UNITSYNCER_HOME}/frontend/parser/languages.so", "java")
