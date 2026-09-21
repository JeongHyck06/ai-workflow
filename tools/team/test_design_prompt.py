import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import design_prompt
import tech_stack
import documents


class DesignPromptTests(unittest.TestCase):
    def test_prompt_is_shared_and_separate_from_stack(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(tech_stack.launch,'ROOT',Path(folder)):
            initial=design_prompt.read()
            self.assertIn('분위기',initial['content'])
            saved=design_prompt.save(dict(content='# 요청\n블루 톤, 모바일 우선',revision=initial['revision']))
            self.assertEqual(documents.read(design_prompt.PATH)['content'],saved['content'])
            self.assertEqual(tech_stack.read()['revision'],'')
            documents.save(dict(path=design_prompt.PATH,content='새 디자인',revision=saved['revision']))
            self.assertEqual(design_prompt.read()['content'],'새 디자인')
            with self.assertRaises(RuntimeError):
                design_prompt.save(dict(content='오래된 변경',revision=saved['revision']))
