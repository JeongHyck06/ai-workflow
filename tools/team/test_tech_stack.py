import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import tech_stack
import documents


class StackTests(unittest.TestCase):
    def test_shared_document_roundtrip_and_conflict(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(tech_stack.launch,'ROOT',Path(folder)):
            initial=tech_stack.read()
            saved=tech_stack.save(dict(content='# 기술스택\nReact + FastAPI',revision=initial['revision']))
            self.assertEqual(documents.read(tech_stack.PATH)['content'],saved['content'])
            documents.save(dict(path=tech_stack.PATH,content='# 기술스택\nVue',revision=saved['revision']))
            self.assertIn('Vue',tech_stack.read()['content'])
            with self.assertRaises(RuntimeError):
                tech_stack.save(dict(content='old edit',revision=saved['revision']))

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(tech_stack.launch,'ROOT',Path(folder)):
            outside=Path(folder)/'outside';outside.mkdir()
            (Path(folder)/'docs').symlink_to(outside)
            with self.assertRaises(ValueError):tech_stack.save(dict(content='bad',revision=''))
            self.assertEqual(list(outside.iterdir()),[])
