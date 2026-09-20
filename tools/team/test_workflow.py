import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import project

spec=importlib.util.spec_from_file_location('workflow',project.WORKFLOW/'workflow.py')
workflow=importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class WorkflowTests(unittest.TestCase):
    def test_existing_team_is_reused_and_summary_completes(self):
        import launch
        with tempfile.TemporaryDirectory() as temp, patch.object(launch, 'STATE', Path(temp)), \
                patch.object(launch.shutil, 'which', return_value='/bin/true'), \
                patch.object(launch.sys, 'platform', 'darwin'), \
                patch.object(launch, 'status_for', return_value=('RUNNING', {})), \
                patch.object(launch, 'bg_names', return_value=set()), \
                patch.object(launch, 'start_bg') as start, patch('builtins.print'):
            self.assertEqual(launch.launch('claude'), 0)
            start.assert_not_called()

    def test_initialization_is_repeatable_and_preserves_existing_rules(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()/'todo';rules=root/'docs/agents/GIT.md'
            rules.parent.mkdir(parents=True);rules.write_text('existing PR rules')
            with patch.object(project,'CONFIG',Path(temp)/'config.json'):
                workflow.initialize(root)
                workflow.initialize(root)
            self.assertEqual(rules.read_text(),'existing PR rules')
            self.assertTrue((root/'app').is_dir())
            self.assertTrue((root/'backend').is_dir())
            self.assertNotIn('## ISSUE-0001',(root/'docs/issues/ACTIVE.md').read_text())
            self.assertNotIn('wSs0xJpVRe6B8TNEy0kL2G',(root/'docs/product/DESIGN_SYSTEM.md').read_text())
            self.assertEqual((root/'.gitignore').read_text().count('/.team-runtime/'),1)
            self.assertIn(str(root),(root/'.agents/skills/setup/SKILL.md').read_text())

    def test_project_configuration_and_environment_are_isolated(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(project,'CONFIG',Path(temp)/'config.json'), patch.dict('os.environ',{},clear=True):
            self.assertEqual(project.root(),project.WORKFLOW)
            with patch.dict('os.environ',{'TEAM_PROJECT_ROOT':temp}):self.assertEqual(project.root(),Path(temp).resolve())

    def test_default_pr_rules_match_original(self):
        self.assertEqual((project.WORKFLOW/'docs/agents/GIT.md').read_bytes(),(project.WORKFLOW/'templates/project/docs/agents/GIT.md').read_bytes())

    def test_same_named_projects_have_distinct_role_names(self):
        self.assertNotEqual(project.session_prefix(Path('/one/todo')),project.session_prefix(Path('/two/todo')))
        self.assertEqual(project.session_prefix(project.WORKFLOW),'vive')

    def test_fresh_clone_starts_for_parent_project_without_inherited_data(self):
        import json
        import os
        import select
        import shutil
        import subprocess
        import sys
        import time
        from urllib.request import urlopen
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()/'todo';clone=root/'workflow';clone.mkdir(parents=True)
            shutil.copy2(project.WORKFLOW/'workflow.py',clone/'workflow.py')
            for name in ('tools','templates'):
                shutil.copytree(project.WORKFLOW/name,clone/name,ignore=shutil.ignore_patterns('__pycache__'))
            env=os.environ.copy();env.pop('TEAM_PROJECT_ROOT',None)
            process=subprocess.Popen([sys.executable,str(clone/'workflow.py'),'start','--port','0'],
                                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
            try:
                output=b'';deadline=time.monotonic()+10
                while b'Team Monitor: http://' not in output and time.monotonic()<deadline:
                    if select.select([process.stdout],[],[],.2)[0]:output+=os.read(process.stdout.fileno(),4096)
                self.assertIn(b'Team Monitor: http://',output)
                url=output.decode().split('Team Monitor: ')[-1].strip()
                with urlopen(url+'/api/resources',timeout=3) as response:data=json.load(response)
                self.assertEqual(data['root'],str(root))
                self.assertEqual(data['secrets'],[])
                self.assertEqual(data['links'],dict(git='',figma='',deploy=''))
                self.assertTrue((root/'app').is_dir())
                self.assertTrue((root/'backend').is_dir())
                self.assertIn('- 현재 등록된 Issue: 없음',(root/'docs/issues/ACTIVE.md').read_text())
                self.assertEqual((root/'docs/agents/GIT.md').read_bytes(),(project.WORKFLOW/'docs/agents/GIT.md').read_bytes())
            finally:
                process.terminate();process.wait(timeout=5)
                process.stdout.close();process.stderr.close()
