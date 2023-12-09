import json
from typing import Iterable
import fire
import os
from tree_sitter.binding import Node
from frontend.parser import RUST_LANGUAGE
from frontend.parser.ast_util import ASTUtil
from unitsyncer.util import replace_tabs
import json
from evaluation.rust.compile import flatten_use_delc
import unittest
import os
import logging


class TestRustCompile(unittest.TestCase):
    def test_flatten_base64(self):
        code = "use rand::{Rng, SeedableRng};"
        expected = ["use rand::Rng;", "use rand::SeedableRng;"]
        self.assertEqual(flatten_use_delc(code), expected)

        code = "use base64::engine::{general_purpose::STANDARD, Engine};"
        expected = [
            "use base64::engine::general_purpose::STANDARD;",
            "use base64::engine::Engine;",
        ]
        self.assertEqual(flatten_use_delc(code), expected)

        code = "use base64::engine::general_purpose::{GeneralPurpose, NO_PAD};"
        expected = [
            "use base64::engine::general_purpose::GeneralPurpose;",
            "use base64::engine::general_purpose::NO_PAD;",
        ]
        self.assertEqual(flatten_use_delc(code), expected)

        # use wildcard only
        code = "use base64::*;"
        expected = ["use base64::*;"]
        self.assertEqual(flatten_use_delc(code), expected)

        # use wildcard in list
        code = "use base64::{alphabet::URL_SAFE, engine::general_purpose::PAD, engine::general_purpose::STANDARD, *,};"
        expected = [
            "use base64::alphabet::URL_SAFE;",
            "use base64::engine::general_purpose::PAD;",
            "use base64::engine::general_purpose::STANDARD;",
            "use base64::*;",
        ]
        self.assertEqual(flatten_use_delc(code), expected)

        # use_as clause in list
        code = "use base64::{engine::general_purpose::STANDARD, Engine as _};"
        expected = [
            "use base64::engine::general_purpose::STANDARD;",
            "use base64::Engine as _;",
        ]
        self.assertEqual(flatten_use_delc(code), expected)

        # with indent
        code = """
use base64::{
    alphabet::URL_SAFE, engine::general_purpose::PAD, engine::general_purpose::STANDARD, *,
};"""
        expected = [
            "use base64::alphabet::URL_SAFE;",
            "use base64::engine::general_purpose::PAD;",
            "use base64::engine::general_purpose::STANDARD;",
            "use base64::*;",
        ]
        self.assertEqual(flatten_use_delc(code), expected)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
