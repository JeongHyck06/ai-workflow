import unittest
from unittest.mock import patch, MagicMock
import qa_logs


class QALogTests(unittest.TestCase):
    def test_pagination_and_exact_role_project_identity(self):
        root = str(qa_logs.launch.ROOT)
        qa = dict(id='qa', cwd=root, preview='이 프로젝트의 QA 역할 세션이다.', createdAt=5,
                  updatedAt=8, turns=[{'items': [{'type': 'agentMessage', 'text': '<script>literal</script>'}]}])
        reader = MagicMock()
        reader.request.side_effect = [dict(data=[dict(qa, id='other', cwd='/other'),dict(qa,id='pm',preview='PM')], nextCursor='page2'),
                                      dict(data=[qa],nextCursor=None), dict(thread=qa)]
        with patch('qa_logs.Reader') as factory:
            factory.return_value.__enter__.return_value = reader
            result = qa_logs.read()
        self.assertEqual(result['session'], 'qa')
        self.assertIn('<script>literal</script>', result['log'])
        self.assertEqual(reader.request.call_args.args, ('thread/read',dict(threadId='qa',includeTurns=True)))

    def test_changed_identity_rejected(self):
        qa = dict(id='qa',cwd=str(qa_logs.launch.ROOT),preview='이 프로젝트의 QA 역할 세션이다.')
        reader=MagicMock()
        reader.request.side_effect=[dict(data=[qa]),dict(thread=dict(qa,cwd='/other'))]
        with patch('qa_logs.Reader') as factory:
            factory.return_value.__enter__.return_value=reader
            with self.assertRaises(RuntimeError):qa_logs.read()

    def test_read_only_and_private_reasoning_not_rendered(self):
        with self.assertRaises(ValueError):qa_logs.Reader().request('turn/start',{})
        self.assertNotIn('private',qa_logs.format_history({'turns':[{'items':[{'type':'reasoning','text':'private'}]}]}))

    def test_failure_does_not_claim_role_stopped(self):
        row={}
        with patch('qa_logs.launch.status_for',return_value=('RUNNING',{})), patch('qa_logs.launch.STATE') as state, patch('qa_logs.read',side_effect=RuntimeError('fail')):
            state.exists.return_value=True
            qa_logs.populate(row)
        self.assertEqual(row['status'],'RUNNING')
        self.assertIn('조회할 수 없습니다',row['message'])
