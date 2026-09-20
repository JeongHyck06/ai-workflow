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
    def test_start_launches_team_then_monitor(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {}, clear=True), \
                patch.object(workflow.sys, 'argv', ['workflow.py', 'start', '--project', temp]), \
                patch.object(workflow, 'initialize') as initialize, \
                patch.object(workflow.socket, 'socket'), \
                patch.object(workflow.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as team, \
                patch.object(workflow.os, 'execv') as monitor:
            workflow.main()
            initialize.assert_called_once_with(Path(temp).resolve())
            self.assertIn('team', team.call_args.args[0])
            self.assertEqual(team.call_args.kwargs['cwd'], workflow.WORKFLOW)
            self.assertIn(str(workflow.WORKFLOW/'tools/team/dashboard.py'),monitor.call_args.args[1])

    def test_roles_use_tool_cwd_and_explicit_product_paths(self):
        import launch
        with patch.object(launch,'PRODUCT_ROOT',Path('/products/todo')):
            prompt=launch.prompt_for('pm')
            self.assertIn('/products/todo/frontend',prompt)
            self.assertIn('/products/todo/backend',prompt)
            self.assertIn(str(launch.ROOT),launch.command_for('qa','codex'))
            self.assertEqual(launch.clean_env()['TEAM_PROJECT_ROOT'],'/products/todo')

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

    def test_initialization_is_repeatable_and_keeps_files_inside_workflow(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()/'todo';clone=root/'ai-workflow'
            clone.mkdir(parents=True)
            shutil.copytree(project.WORKFLOW/'templates',clone/'templates')
            rules=clone/'docs/agents/GIT.md'
            rules.parent.mkdir(parents=True);rules.write_text('existing tool docs')
            with patch.object(workflow,'WORKFLOW',clone), patch.object(project,'CONFIG',clone/'.workflow-project.json'):
                workflow.initialize(root)
                rules.write_text('project PR rules')
                workflow.initialize(root)
            self.assertEqual(rules.read_text(),'project PR rules')
            self.assertEqual({p.name for p in root.iterdir()},{'ai-workflow','frontend','backend'})
            self.assertEqual((clone/'.team-runtime/bootstrap-backup/docs/agents/GIT.md').read_text(),'existing tool docs')
            self.assertNotIn('## ISSUE-0001',(clone/'docs/issues/ACTIVE.md').read_text())
            self.assertIn(str(root/'frontend'),(clone/'docs/agents/FRONTEND.md').read_text())
            self.assertEqual((clone/'.gitignore').read_text().count('/.team-runtime/'),1)

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
            process=subprocess.Popen([sys.executable,str(clone/'workflow.py'),'start','--monitor-only','--port','0'],
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
                self.assertTrue((root/'frontend').is_dir())
                self.assertTrue((root/'backend').is_dir())
                self.assertEqual({p.name for p in root.iterdir()},{'workflow','frontend','backend'})
                self.assertIn('- 현재 등록된 Issue: 없음',(clone/'docs/issues/ACTIVE.md').read_text())
                self.assertEqual((clone/'docs/agents/GIT.md').read_bytes(),(project.WORKFLOW/'docs/agents/GIT.md').read_bytes())
            finally:
                process.terminate();process.wait(timeout=5)
                process.stdout.close();process.stderr.close()
