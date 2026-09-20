import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import documents


class DocumentsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        (self.root/'docs/agents').mkdir(parents=True)
        (self.root/'docs/agents/GIT.md').write_text('# Git\n\nCommit rules',encoding='utf-8')
        (self.root/'MyIdea.md').write_text('# Idea',encoding='utf-8')
        (self.root/'secret.txt').write_text('private',encoding='utf-8')
        self.mock=patch.object(documents.launch,'ROOT',self.root)
        self.mock.start()

    def tearDown(self):
        self.mock.stop()
        self.temp.cleanup()

    def test_index_classifies_rules_and_draft(self):
        docs=documents.index()
        self.assertEqual(len(docs),2)
        self.assertTrue(any(d['path']=='docs/agents/GIT.md' for d in docs))
        self.assertFalse(any(d['path']=='secret.txt' for d in docs))

    def test_document_reads_latest_file(self):
        path='docs/agents/GIT.md'
        documents.read(path)
        (self.root/path).write_text('# Updated',encoding='utf-8')
        self.assertEqual(documents.read(path)['content'],'# Updated')

    def test_traversal_and_absolute_paths_blocked(self):
        for value in ['../secret.txt','docs/../secret.txt',str(self.root/'secret.txt'),'/etc/passwd']:
            with self.assertRaises(FileNotFoundError):documents.read(value)

    def test_symlink_outside_docs_blocked(self):
        (self.root/'docs/leak.md').symlink_to(self.root/'secret.txt')
        with self.assertRaises(FileNotFoundError):documents.read('docs/leak.md')
