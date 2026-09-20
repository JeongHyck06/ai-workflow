"""Resolve the monitored project independently of the workflow checkout."""
import json
import os
import hashlib
import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[2]
CONFIG = WORKFLOW / '.workflow-project.json'


def session_prefix(target):
    target = target.resolve()
    label = re.sub(r'[^a-zA-Z0-9-]', '-', target.name).strip('-')[:20] or 'project'
    digest = hashlib.sha256(str(target).encode()).hexdigest()[:8]
    return 'wf-' + label + '-' + digest


def root():
    value = os.environ.get('TEAM_PROJECT_ROOT')
    if not value and CONFIG.exists():
        value = json.loads(CONFIG.read_text())['project']
    return Path(value).expanduser().resolve() if value else WORKFLOW
