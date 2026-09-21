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

    def test_save_and_conflict_preserve_newer_content(self):
        path='docs/agents/GIT.md'
        old=documents.read(path)
        saved=documents.save(dict(path=path,content='# Saved',revision=old['revision']))
        self.assertEqual(saved['content'],'# Saved')
        with self.assertRaises(RuntimeError):
            documents.save(dict(path=path,content='overwrite',revision=old['revision']))
        self.assertEqual(documents.read(path)['content'],'# Saved')

    def test_save_cannot_write_arbitrary_files(self):
        with self.assertRaises(FileNotFoundError):
            documents.save(dict(path='../secret.txt',content='bad',revision=''))
        self.assertEqual((self.root/'secret.txt').read_text(),'private')

    def test_index_revision_detects_content_change_with_same_timestamp(self):
        import os
        path=self.root/'docs/agents/GIT.md'
        before=next(d for d in documents.index() if d['path']=='docs/agents/GIT.md')
        stamp=path.stat()
        path.write_text('# New rules')
        os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        after=next(d for d in documents.index() if d['path']=='docs/agents/GIT.md')
        self.assertNotEqual(before['revision'],after['revision'])
        self.assertEqual(after['revision'],documents.read('docs/agents/GIT.md')['revision'])
