import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import resources


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name)
        p=patch.object(resources.launch,'STATE',self.root/'.team-runtime');p.start();self.addCleanup(p.stop)
        p=patch('resources.git_url',return_value='');p.start();self.addCleanup(p.stop)

    def test_secret_roundtrip_mask_permissions_and_delete(self):
        resources.update(dict(action='save-secret',name='TEST_KEY',value='test-only-value'))
        self.assertNotIn('test-only-value',json.dumps(resources.overview()))
        self.assertEqual(stat.S_IMODE((resources.launch.STATE/'resources.json').stat().st_mode),0o600)
        self.assertEqual(resources.update(dict(action='reveal-secret',name='TEST_KEY'))['value'],'test-only-value')
        resources.update(dict(action='save-secret',name='TEST_KEY',value='replacement'))
        self.assertEqual(resources.update(dict(action='reveal-secret',name='TEST_KEY'))['value'],'replacement')
        resources.update(dict(action='delete-secret',name='TEST_KEY'))
        self.assertEqual(resources.overview()['secrets'],[])

    def test_url_and_key_validation(self):
        for value in ['javascript:alert(1)','https://user:pass@example.com','file:///tmp/key']:
            with self.assertRaises(ValueError):resources.valid_url(value)
        with self.assertRaises(ValueError):resources.update(dict(action='save-secret',name='../x',value='v'))
        resources.update(dict(action='links',links=dict(git='https://github.com/org/repo',figma='',deploy='')))
        self.assertEqual(resources.overview()['links']['git'],'https://github.com/org/repo')

    def test_symlink_store_rejected_and_no_external_write(self):
        outside=self.root/'outside';outside.write_text('original')
        resources.launch.STATE.mkdir()
        (resources.launch.STATE/'resources.json').symlink_to(outside)
        with self.assertRaises(ValueError):resources.update(dict(action='save-secret',name='KEY',value='v'))
        self.assertEqual(outside.read_text(),'original')

    def test_repository_links_are_independent(self):
        resources.update(dict(action='links',links=dict(backend='https://github.com/org/backend',frontend='https://github.com/org/frontend',app='https://github.com/org/app')))
        links=resources.overview()['links']
        self.assertEqual(links['backend'],'https://github.com/org/backend')
        self.assertEqual(links['frontend'],'https://github.com/org/frontend')
        self.assertEqual(links['app'],'https://github.com/org/app')
