from tree_sitter import Language, Parser, Tree
from unitsyncer.common import UNITSYNCER_HOME

SHARED_LIB = f"{UNITSYNCER_HOME}/frontend/parser/languages.so"
JAVA_LANGUAGE = Language(SHARED_LIB, "java")
JAVASCRIPT_LANGUAGE = Language(SHARED_LIB, "javascript")
RUST_LANGUAGE = Language(SHARED_LIB, "rust")
GO_LANGUAGE = Language(SHARED_LIB, "go")
CPP_LANGUAGE = Language(SHARED_LIB, "cpp")
