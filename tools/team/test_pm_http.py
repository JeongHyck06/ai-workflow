"""Local HTTP contract checks; no model sessions receive test messages."""
import json
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch, MagicMock
from http.server import ThreadingHTTPServer
import dashboard


class PMHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),dashboard.Handler)
        cls.base='http://127.0.0.1:'+str(cls.server.server_port)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, path, body, token=None, origin=None):
        headers={'Content-Type':'application/json','Origin':origin or self.base}
        if token:headers['X-Team-Token']=token
        return urlopen(Request(self.base+path, data=json.dumps(body).encode(),headers=headers),timeout=5)

    def test_unauthorized_input_does_not_write(self):
        for token, origin in [(None,self.base),(dashboard.csrf_token,'https://other.example')]:
            with patch.object(dashboard.connections,'get') as get:
                with self.assertRaises(HTTPError) as result:
                    self.post('/api/pm/input',{'connection':'x','data':'hello'},token,origin)
                self.assertEqual(result.exception.code,403)
                get.assert_not_called()

    def test_valid_input_and_output_contract(self):
        terminal=MagicMock()
        terminal.poll.return_value={'output':'aGVsbG8=','closed':False}
        with patch.object(dashboard.connections,'get',return_value=terminal):
            with self.post('/api/pm/input',{'connection':'x','data':'hello\r'},dashboard.csrf_token) as response:
                self.assertTrue(json.load(response)['ok'])
            terminal.write.assert_called_once_with('hello\r')
            with urlopen(self.base+'/api/pm/output?connection=x') as response:
                self.assertEqual(json.load(response)['output'],'aGVsbG8=')

    def test_other_role_endpoint_rejected(self):
        with self.assertRaises(HTTPError) as result:
            self.post('/api/frontend/input',{'connection':'x','data':'hello'},dashboard.csrf_token)
        self.assertEqual(result.exception.code,404)

    def test_oversized_payload_rejected(self):
        with self.assertRaises(HTTPError) as result:
            self.post('/api/pm/input',{'connection':'x','data':'x'*17000},dashboard.csrf_token)
        self.assertEqual(result.exception.code,400)

    def test_secrets_require_origin_and_token_and_are_not_in_get(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder, patch.object(dashboard.launch,'STATE',Path(folder)), patch('resources.git_url',return_value=''):
            body=dict(action='save-secret',name='TEST_KEY',value='http-test-secret')
            with self.assertRaises(HTTPError) as result:self.post('/api/resources',body)
            self.assertEqual(result.exception.code,403)
            with self.post('/api/resources',body,dashboard.csrf_token) as response:self.assertTrue(json.load(response)['ok'])
            with urlopen(self.base+'/api/resources') as response:
                self.assertNotIn('http-test-secret',response.read().decode())
            with self.assertRaises(HTTPError):self.post('/api/resources',dict(action='reveal-secret',name='TEST_KEY'),dashboard.csrf_token,'https://other.example')
            with self.post('/api/resources',dict(action='reveal-secret',name='TEST_KEY'),dashboard.csrf_token) as response:
                self.assertEqual(response.headers['Cache-Control'],'no-store')
                self.assertEqual(json.load(response)['value'],'http-test-secret')

class TerminalLifecycleTests(unittest.TestCase):
    def test_attach_client_close_does_not_hang(self):
        import subprocess
        import time
        from pm_terminal import Terminal
        real_popen=subprocess.Popen
        def local_echo(args, **kwargs):
            return real_popen(['/bin/cat'], **kwargs)
        with patch('pm_terminal.subprocess.Popen', side_effect=local_echo):
            terminal=Terminal('unused', 'unused')
            terminal.write('transport test\n')
            deadline=time.monotonic()+2
            received=b''
            import base64
            while time.monotonic()<deadline:
                received+=base64.b64decode(terminal.poll()['output'])
                if b'transport test' in received:break
                time.sleep(.01)
            self.assertIn(b'transport test',received)
            closer=threading.Thread(target=terminal.close,daemon=True)
            closer.start()
            closer.join(3)
            self.assertFalse(closer.is_alive())
            self.assertTrue(terminal.closed)
