import unittest

from forge\_assist.patch import parse\_file\_plan


class ParseFilePlanTests(unittest.TestCase):
    def test\_parses\_valid\_plan(self):
        summary, files = parse\_file\_plan(
            '{"summary":"Add a file","files":[{"path":"hello.txt","content":"Hi"}]}'
        )
        self.assertEqual(summary, "Add a file")
        self.assertEqual(files, [{"path": "hello.txt", "content": "Hi"}])

    def test\_parses\_json\_code\_fence(self):
        response = """```json
{"summary":"Update","files":[{"path":"app.py","content":"print(1)"}]}
```"""
        summary, files = parse\_file\_plan(response)
        self.assertEqual(summary, "Update")
        self.assertEqual(files[0]["path"], "app.py")

    def test\_rejects\_empty\_file\_list(self):
        with self.assertRaises(ValueError):
            parse\_file\_plan('{"summary":"Nothing","files":[]}')

    def test\_rejects\_duplicate\_paths(self):
        response = (
            '{"summary":"Duplicate","files":['
            '{"path":"a.txt","content":"one"},'
            '{"path":"a.txt","content":"two"}]}'
        )
        with self.assertRaises(ValueError):
            parse\_file\_plan(response)


if __name__ == "\_\_main\_\_":
    unittest.main()
