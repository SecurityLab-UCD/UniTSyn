from tree_sitter import Language, Parser, Tree
from unitsyncer.common import UNITSYNCER_HOME


JAVA_LANGUAGE = Language(f"{UNITSYNCER_HOME}/frontend/parser/languages.so", "java")
JAVASCRIPT_LANGUAGE = Language(f"{UNITSYNCER_HOME}/frontend/parser/languages.so", "javascript")
RUST_LANGUAGE = Language(f"{UNITSYNCER_HOME}/frontend/parser/languages.so", "rust")