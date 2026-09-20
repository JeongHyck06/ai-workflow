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
    def test_any_archive_folder_name_defaults_to_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()/'Test Todo'
            for name in ('ai-workflow-main','ai-workflow-dev','my tools'):
                clone=root/name
                with patch.object(workflow,'WORKFLOW',clone),patch.object(project,'CONFIG',clone/'.workflow-project.json'):
                    self.assertEqual(workflow.default_project(),root)

    def test_wrong_saved_zip_root_is_repaired_with_code_preserved(self):
        import json
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()/'Test Todo';clone=root/'ai-workflow-main'
            clone.mkdir(parents=True)
            shutil.copytree(project.WORKFLOW/'templates',clone/'templates')
            for name in ('app','backend'):
                (clone/name).mkdir();(clone/name/'code.txt').write_text(name+' code')
            config=clone/'.workflow-project.json';config.write_text(json.dumps(dict(project=str(clone),layout=2)))
            with patch.object(workflow,'WORKFLOW',clone),patch.object(project,'CONFIG',config):
                self.assertEqual(workflow.default_project(),root)
                workflow.initialize(workflow.default_project())
                workflow.initialize(workflow.default_project())
            self.assertEqual({p.name for p in root.iterdir()},{'ai-workflow-main','app','backend'})
            for name in ('app','backend'):
                self.assertFalse((clone/name).exists())
                self.assertEqual((root/name/'code.txt').read_text(),name+' code')
            self.assertEqual(json.loads(config.read_text())['project'],str(root))

    def test_legacy_code_conflict_leaves_both_sides_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();clone=root/'ai-workflow-main'
            for folder in (clone/'app',root/'app',clone/'backend'):
                folder.mkdir(parents=True);(folder/'code').write_text(str(folder))
            with patch.object(workflow,'WORKFLOW',clone):
                with self.assertRaisesRegex(ValueError,'모두 있습니다'):workflow.relocate_legacy_code(root)
            self.assertTrue((clone/'app/code').exists())
            self.assertTrue((root/'app/code').exists())
            self.assertTrue((clone/'backend/code').exists())

    def test_shipped_skill_symlink_and_failed_initialization_retry(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()/'todo';clone=root/'ai-workflow'
            clone.mkdir(parents=True)
            shutil.copytree(project.WORKFLOW/'templates',clone/'templates')
            link=clone/'.agents/skills/setup/SKILL.md'
            link.parent.mkdir(parents=True)
            link.symlink_to('../../../.claude/skills/setup/SKILL.md')
            backup=clone/'.team-runtime/bootstrap-backup/docs'
            backup.mkdir(parents=True);(backup/'README.md').write_text('original tool docs')
            docs=clone/'docs';docs.mkdir();(docs/'README.md').write_text('preserved project docs')
            with patch.object(workflow,'WORKFLOW',clone),patch.object(project,'CONFIG',clone/'.workflow-project.json'):
                workflow.initialize(root)
                workflow.initialize(root)
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.read_text(),(clone/'.claude/skills/setup/SKILL.md').read_text())
            self.assertEqual((docs/'README.md').read_text(),'preserved project docs')
            self.assertEqual((backup/'README.md').read_text(),'original tool docs')
            self.assertEqual({p.name for p in root.iterdir()},{'ai-workflow','app','backend'})

    def test_external_skill_link_rejected_before_modifying_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()/'todo';clone=root/'ai-workflow'
            link=clone/'.agents/skills/setup/SKILL.md';link.parent.mkdir(parents=True)
            outside=Path(temp)/'outside.md';outside.write_text('untouched')
            link.symlink_to(outside)
            with patch.object(workflow,'WORKFLOW',clone),patch.object(project,'CONFIG',clone/'.workflow-project.json'):
                with self.assertRaisesRegex(ValueError,'폴더 밖'):workflow.initialize(root)
            self.assertEqual(outside.read_text(),'untouched')
            self.assertFalse((clone/'.team-runtime').exists())
            self.assertFalse((root/'app').exists())

    def test_shipped_skill_link_resolves_inside_repository(self):
        targets=workflow.skill_targets()
        self.assertEqual(targets[0],targets[1])
        self.assertTrue(targets[0].is_file())

    def test_start_delegates_team_start_to_live_monitor(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {}, clear=True), \
                patch.object(workflow.sys, 'argv', ['workflow.py', 'start', '--project', temp]), \
                patch.object(workflow, 'initialize') as initialize, \
                patch.object(workflow.os, 'execv') as monitor:
            workflow.main()
            initialize.assert_called_once_with(Path(temp).resolve())
            command = monitor.call_args.args[1]
            self.assertIn('--launch-team', command)
            self.assertNotIn('--port', command)
            self.assertIn(str(workflow.WORKFLOW/'tools/team/dashboard.py'), command)

    def test_roles_use_tool_cwd_and_explicit_product_paths(self):
        import launch
        with patch.object(launch,'PRODUCT_ROOT',Path('/products/todo')):
            prompt=launch.prompt_for('pm')
            self.assertIn('/products/todo/app',prompt)
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
            self.assertEqual({p.name for p in root.iterdir()},{'ai-workflow','app','backend'})
            self.assertEqual((clone/'.team-runtime/bootstrap-backup/docs/agents/GIT.md').read_text(),'existing tool docs')
            self.assertNotIn('## ISSUE-0001',(clone/'docs/issues/ACTIVE.md').read_text())
            self.assertIn(str(root/'app'),(clone/'docs/agents/FRONTEND.md').read_text())
            self.assertEqual((clone/'.gitignore').read_text().count('/.team-runtime/'),1)

    def test_project_configuration_and_environment_are_isolated(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(project,'CONFIG',Path(temp)/'config.json'), patch.dict('os.environ',{},clear=True):
            self.assertEqual(project.root(),project.WORKFLOW)
            with patch.dict('os.environ',{'TEAM_PROJECT_ROOT':temp}):self.assertEqual(project.root(),Path(temp).resolve())

    def test_default_pr_rules_match_original(self):
        self.assertEqual((project.WORKFLOW/'docs/agents/GIT.md').read_bytes(),(project.WORKFLOW/'templates/project/docs/agents/GIT.md').read_bytes())

    def test_same_named_projects_have_distinct_role_names(self):
        self.assertNotEqual(project.session_prefix(Path('/one/todo')),project.session_prefix(Path('/two/todo')))
        self.assertNotEqual(project.session_prefix(project.WORKFLOW),'vive')

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
                self.assertTrue((root/'app').is_dir())
                self.assertTrue((root/'backend').is_dir())
                self.assertEqual({p.name for p in root.iterdir()},{'workflow','app','backend'})
                self.assertIn('- 현재 등록된 Issue: 없음',(clone/'docs/issues/ACTIVE.md').read_text())
                self.assertEqual((clone/'docs/agents/GIT.md').read_bytes(),(project.WORKFLOW/'docs/agents/GIT.md').read_bytes())
            finally:
                process.terminate();process.wait(timeout=5)
                process.stdout.close();process.stderr.close()

    def test_two_monitors_are_isolated_and_repeat_start_reuses_url(self):
        import json
        import os
        import select
        import shutil
        import subprocess
        import sys
        import time
        from urllib.request import urlopen
        with tempfile.TemporaryDirectory() as temp:
            processes = []
            urls = []
            try:
                for name in ('one', 'two'):
                    root = Path(temp).resolve()/name/'todo'
                    clone = root/'ai-workflow-main'
                    clone.mkdir(parents=True)
                    shutil.copy2(project.WORKFLOW/'workflow.py', clone/'workflow.py')
                    for folder in ('tools', 'templates'):
                        shutil.copytree(project.WORKFLOW/folder, clone/folder,
                                        ignore=shutil.ignore_patterns('__pycache__'))
                    command = [sys.executable, str(clone/'workflow.py'), 'start', '--monitor-only']
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    processes.append(process)
                    output = b''
                    deadline = time.monotonic()+10
                    while b'Team Monitor: http://' not in output and time.monotonic()<deadline:
                        if select.select([process.stdout], [], [], .2)[0]:
                            output += os.read(process.stdout.fileno(), 4096)
                    self.assertIn(b'Team Monitor: http://', output)
                    url = output.decode().split('Team Monitor: ')[-1].splitlines()[0]
                    urls.append(url)
                    with urlopen(url+'/api/resources', timeout=3) as response:
                        self.assertEqual(json.load(response)['root'], str(root))
                    repeated = subprocess.run(command, capture_output=True, text=True, timeout=10)
                    self.assertEqual(repeated.returncode, 0, repeated.stderr)
                    self.assertIn('이미 실행 중입니다. Team Monitor: '+url, repeated.stdout)
                self.assertNotEqual(*urls)
            finally:
                for process in processes:
                    process.terminate()
                    process.wait(timeout=5)
                    process.stdout.close()
                    process.stderr.close()
