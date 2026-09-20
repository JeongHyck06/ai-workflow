import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import dashboard


class DashboardTests(unittest.TestCase):
    def setUp(self):
        patcher = patch('qa_logs.read', return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_filters_projects_and_uses_live_id(self):
        calls = []
        def run(args):
            calls.append(args)
            if args[1] == 'agents':
                return json.dumps([
                    dict(id='correct', name=dashboard.launch.session_name('pm'), cwd=str(dashboard.launch.ROOT), kind='background'),
                    dict(id='other', name=dashboard.launch.session_name('frontend'), cwd='/other', kind='background')])
            return '\x1b[32mhello\x1b[0m <script>example</script>'
        with tempfile.TemporaryDirectory() as folder, patch.object(dashboard.launch, 'STATE', Path(folder)), patch.object(dashboard, 'command', run), patch.object(dashboard.shutil, 'which', return_value='claude'):
            rows = {r['role']:r for r in dashboard.snapshot()['roles']}
        self.assertEqual(rows['pm']['status'], 'RUNNING')
        self.assertEqual(rows['pm']['session'], 'correct')
        self.assertEqual(rows['pm']['log'], 'hello <script>example</script>')
        self.assertEqual(rows['frontend']['status'], 'NOT_STARTED')
        self.assertFalse(any('other' in c for c in calls))
        self.assertTrue(rows['qa']['message'])

    def test_foreign_saved_session_is_not_read(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(dashboard.launch, 'STATE', Path(folder)), \
                patch.object(dashboard, 'command', return_value='[]') as command, \
                patch.object(dashboard.shutil, 'which', return_value='claude'):
            (Path(folder)/'pm.json').write_text(json.dumps(dict(
                session='foreign-session', project='/other',
                sessionName=dashboard.launch.session_name('pm'))))
            rows = {r['role']:r for r in dashboard.snapshot()['roles']}
            self.assertEqual(rows['pm']['session'], '')
            self.assertFalse(any('foreign-session' in call.args[0] for call in command.call_args_list))

    def test_cli_failure_is_unknown(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(dashboard.launch, 'STATE', Path(folder)), patch.object(dashboard, 'command', side_effect=RuntimeError('offline')), patch.object(dashboard.shutil, 'which', return_value='claude'):
            state = dashboard.snapshot()
        self.assertTrue(state['error'])
        self.assertTrue(all(r['status']=='UNKNOWN' for r in state['roles'] if r['provider']=='claude'))

    def test_missing_cli_and_corrupt_state_do_not_crash(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(dashboard.launch, 'STATE', Path(folder)), patch.object(dashboard.shutil, 'which', return_value=None):
            (Path(folder)/'pm.json').write_text('{')
            self.assertEqual(dashboard.snapshot()['roles'][0]['status'], 'UNKNOWN')

    def test_cache_limits_repeated_queries(self):
        monitor = dashboard.Monitor()
        with patch.object(dashboard, 'snapshot', return_value={'roles':[]}) as read:
            monitor.get()
            monitor.get()
            self.assertEqual(read.call_count, 1)


if __name__ == '__main__':
    unittest.main()

class PMConnectionTests(unittest.TestCase):
    def test_pm_worktree_is_accepted_other_project_is_not(self):
        from pm_terminal import belongs_to_project
        root = dashboard.launch.ROOT
        self.assertTrue(belongs_to_project({'cwd': str(root / '.claude/worktrees/pm-test')}))
        self.assertFalse(belongs_to_project({'cwd': '/other/.claude/worktrees/pm-test'}))

    def test_connection_targets_only_project_pm(self):
        from pm_terminal import Connections
        from types import SimpleNamespace
        manager = Connections()
        sessions = [dict(id='right', name=dashboard.launch.session_name('pm'), cwd=str(dashboard.launch.ROOT / '.claude/worktrees/pm'), kind='background'),
                    dict(id='wrong', name=dashboard.launch.session_name('pm'), cwd='/other', kind='background')]
        with patch('pm_terminal.subprocess.run', return_value=SimpleNamespace(stdout=json.dumps(sessions))), patch('pm_terminal.shutil.which', return_value='claude'), patch('pm_terminal.Terminal') as terminal:
            manager.connect()
            terminal.assert_called_once_with('claude', 'right')

    def test_ambiguous_pm_is_rejected(self):
        from pm_terminal import Connections
        from types import SimpleNamespace
        session = dict(id='a', name=dashboard.launch.session_name('pm'), cwd=str(dashboard.launch.ROOT), kind='background')
        with patch('pm_terminal.subprocess.run', return_value=SimpleNamespace(stdout=json.dumps([session, session]))), patch('pm_terminal.shutil.which', return_value='claude'), patch('pm_terminal.Terminal') as terminal:
            with self.assertRaises(RuntimeError):
                Connections().connect()
            terminal.assert_not_called()
