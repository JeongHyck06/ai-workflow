import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import usage


class UsageTests(unittest.TestCase):
    def test_claude_deduplicates_blocks_and_excludes_other_projects(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'project';base=Path(temp)/'records'
            folder=base/re.sub(r'[^a-zA-Z0-9-]','-',str(root));folder.mkdir(parents=True)
            record=dict(type='assistant',sessionId='one',cwd=str(root),message=dict(id='message1',usage=dict(input_tokens=10,output_tokens=20,cache_read_input_tokens=30,cache_creation_input_tokens=40)))
            (folder/'session.jsonl').write_text('\n'.join(json.dumps(r) for r in [record,record,dict(record,cwd='/other',sessionId='other')]))
            with patch.object(usage.launch,'ROOT',root):result=usage.claude_usage(base)
            self.assertEqual((result['input'],result['output'],result['cached'],result['sessions']),(80,20,30,1))

    def test_codex_uses_last_cumulative_value_and_validates_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);path=base/'session.jsonl'
            lines=[dict(type='session_meta',payload=dict(id='qa',cwd=str(usage.launch.ROOT)))]
            for n in [100,150]:lines.append(dict(type='event_msg',payload=dict(type='token_count',info=dict(total_token_usage=dict(input_tokens=n,output_tokens=20)))))
            path.write_text('\n'.join(json.dumps(r) for r in lines))
            self.assertEqual(usage.codex_file_usage(dict(path=str(path),id='qa'),base)['input_tokens'],150)
            self.assertIsNone(usage.codex_file_usage(dict(path=str(path),id='other'),base))

    def test_missing_records_not_reported_as_zero_usage(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertFalse(usage.claude_usage(Path(temp))['available'])
