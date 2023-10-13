from unitsyncer.sync import Synchronizer
from pylspclient.lsp_structs import LANGUAGE_IDENTIFIER
from returns.maybe import Maybe, Nothing, Some


def main():
    syncer = Synchronizer("./repos/py_example", LANGUAGE_IDENTIFIER.PYTHON)
    syncer.initialize()

    match syncer.get_source_of_call("tests/test_add.py", 4, 13):
        case Some(source):
            print(source)
        case Nothing:
            print("Not found")

    syncer.stop()


if __name__ == "__main__":
    main()
