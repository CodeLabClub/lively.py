# nodemon -x  python -- -m unittest lively/tests/test_interface.py

import sys
from unittest import TestCase
import json

from lively.eval import sync_eval, run_eval
from lively.completions import get_completions
from lively.code_formatting import code_format

from lively.tests.helper import async_test

# runner = unittest.TextTestRunner()
# suite = unittest.TestSuite()
# suite.addTests([EvalTestCase(k) for k,v in EvalTestCase.__dict__.items() if k.startswith("test_")])
# runner.run(suite)


class EvalTestCase(TestCase):

    def test_sync_eval(self):
        result = sync_eval("1+2")
        expected = {'isError': False, 'isEvalResult': True, 'value': '3', "stdout": '', "stderr": ''}
        self.assertEqual(result.json_stringify(), json.dumps(expected))

    def test_eval_in_file(self):
        mod_name = "lively.tests.some-test-module"
        sync_eval("a = 1 + 2", mod_name)
        self.assertEqual(sync_eval("a", mod_name).value, 3,
                         "top-level variable not recorded")
        self.assertEqual(sys.modules.get(mod_name).__dict__.get("a"), 3,
                         "top-level variable not in module dict")

    @async_test
    async def test_async_eval_simple(self):
        result = await run_eval("1 + 2")
        self.assertEqual(result.value, 3)

    @async_test
    async def test_async_eval_await(self):
        async_code = ("import asyncio\n"
                      "import datetime\n"
                      "\n"
                      "async def async_counter(duration, loop=asyncio.get_event_loop()):\n"
                      "    end_time = loop.time() + duration\n"
                      "    counter = 0\n"
                      "    while True:\n"
                      "        counter = counter + 1\n"
                      "        if (loop.time()) >= end_time:\n"
                      "            break\n"
                      "        await asyncio.sleep(0.1)\n"
                      "    return counter\n")

        result = await run_eval(async_code + "await async_counter(0.5)")
        self.assertEqual(result.value, 6)


class CompletionTest(TestCase):

    @async_test
    async def test_get_completions(self):
        completions = await get_completions("import os\nos.p\n", 2, 3, file=None)
        path_compl, = [c for c in completions if c.get("name") == "path"]
        self.assertTrue(
            set({'full_name': 'os.path',
                 'is_keyword': False,
                 'module_name': 'os',
                 'type': 'module'}.items()).issubset(set(path_compl.items())))


class CodeFormatTest(TestCase):

    def test_format_whole_string(self):
        src = "foo(\n1,\n2)"
        formatted = code_format(src, None, "<unknown>", None)
        print(formatted)
        self.assertEqual(formatted, "foo(1, 2)\n")

    def test_format_lines(self):
        src = "hello(1,\n2)\n\nfoo(\n1,\n2)"
        formatted = code_format(src, [(4, 6)], "<unknown>", None)
        self.assertEqual(formatted, "hello(1,\n2)\n\nfoo(1, 2)\n")
