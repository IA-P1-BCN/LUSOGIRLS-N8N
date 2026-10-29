"""Entrada SMTP/IMAP real en GreenMail local; nunca conecta con un buzón personal."""
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path
import json
import smtplib
import time
import uuid

from lab import SECRET, STATE, install, request
from test_08 import activate, executions


def imap_flow(path, error_id, model_mock=True):
    name = 'PF · Buzón IMAP local'
    existing = request('/rest/credentials')['data']
    credential = next((c for c in existing if c['name'] == name and c['type'] == 'imap'), None)
    if credential is None:
        credential = request('/rest/credentials', {
            'name': name,
            'type': 'imap',
            'data': {'user': 'pagos', 'password': SECRET, 'host': 'buzon', 'port': 3143,
                     'secure': False, 'allowUnauthorizedCerts': False},
        })['data']
    flow = json.loads(Path(path).read_text())
    test_run = uuid.uuid4().hex
    for node in flow['nodes']:
        if node['type'] == 'n8n-nodes-base.emailReadImap':
            node['credentials']['imap'] = {'id': credential['id'], 'name': name}
            node['parameters'].setdefault('options', {})['customEmailConfig'] = json.dumps(['UNSEEN', ['HEADER', 'X-PF-Test-Run', test_run]])
        if model_mock and node['name'] == 'Extraer pago':
            node['parameters']['url'] = 'http://simulador:8080/chat/completions'
            node['parameters'].pop('authentication', None)
            node['parameters'].pop('genericAuthType', None)
            node['parameters'].pop('nodeCredentialType', None)
            node.pop('credentials', None)
    file = STATE / ('03-imap-' + uuid.uuid4().hex + '.json')
    file.write_text(json.dumps(flow))
    installed = install(file, error_id)
    try:
        activate(installed)
    except Exception:
        request('/rest/workflows/' + installed['id'] + '/deactivate', {})
        raise
    installed['_test_run'] = test_run
    return installed


def deliver(flow, payload, timeout=90):
    previous = {execution['id'] for execution in executions(flow['id'])}
    message = EmailMessage()
    message['From'] = 'banco@example.test'
    message['To'] = 'pagos@example.test'
    message['Subject'] = payload['subject']
    message['Date'] = formatdate(localtime=False)
    message['Message-ID'] = payload['metadata']['message-id']
    message['X-PF-Test-Run'] = flow['_test_run']
    message.set_content(payload['textPlain'])
    # El mensaje recorre SMTP → buzón → Email Trigger IMAP → subflujo PF-03.
    with smtplib.SMTP('127.0.0.1', 13025, timeout=10) as smtp:
        smtp.send_message(message)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        fresh = [run for run in executions(flow['id']) if run['id'] not in previous]
        terminal = ('success', 'error', 'crashed')
        parents = [run for run in fresh if run.get('mode') == 'trigger']
        children = [run for run in fresh if run.get('mode') == 'integrated']
        if parents and children and all(run.get('status') in terminal for run in fresh):
            assert len(parents) == len(children) == 1, [(r['id'], r.get('mode')) for r in fresh]
            parent, child = parents[0], children[0]
            assert parent['status'] == child['status'], (parent['status'], child['status'])
            return {**child, 'imap_execution': parent['id']}
        time.sleep(.3)
    raise AssertionError('No terminó el recorrido IMAP/subflujo: ' + repr([(r['id'], r.get('mode'), r.get('status')) for r in fresh]))
