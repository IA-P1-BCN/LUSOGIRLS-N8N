"""Evita enviar la credencial de la tienda al proveedor de IA al importar/exportar."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import lab


class CredencialesPorNombre(unittest.TestCase):
    def install_with(self, references):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            (state / 'credentials.json').write_text(json.dumps(references))
            source = Path(__file__).resolve().parents[2] / 'workflows/03-abonos-distancia.json'
            with patch.object(lab, 'STATE', state), patch.object(lab, 'request', side_effect=lambda path, data: {'data': data}):
                return lab.install(source)

    def test_modelo_sin_credencial_no_recibe_la_clave_de_la_api(self):
        flow = self.install_with({'httpHeaderAuth': {'id': 'api-local', 'name': 'PF · API tienda'}})
        model = next(node for node in flow['nodes'] if node['name'] == 'Extraer pago')
        self.assertEqual(model['credentials'], {'openRouterApi': {'name': 'PF · Modelo extracción'}})
        self.assertEqual(model['parameters']['authentication'], 'predefinedCredentialType')
        self.assertEqual(model['parameters']['nodeCredentialType'], 'openRouterApi')
        api = next(node for node in flow['nodes'] if node['name'] == 'Registrar abono')
        self.assertEqual(api['credentials']['httpHeaderAuth']['id'], 'api-local')

    def test_modelo_y_api_conservan_referencias_distintas(self):
        flow = self.install_with({
            'httpHeaderAuth': {'id': 'api-local', 'name': 'PF · API tienda'},
            'PF · Modelo extracción': {'id': 'modelo-local', 'name': 'PF · Modelo extracción'},
        })
        model = next(node for node in flow['nodes'] if node['name'] == 'Extraer pago')
        self.assertEqual(model['credentials']['openRouterApi']['id'], 'modelo-local')
        api = next(node for node in flow['nodes'] if node['name'] == 'Registrar abono')
        self.assertEqual(api['credentials']['httpHeaderAuth']['id'], 'api-local')


    def test_exportacion_conserva_nombres_compartidos_sin_ids(self):
        source = Path(__file__).resolve().parents[2] / 'workflows/03-abonos-distancia.json'
        declared = json.loads(source.read_text())
        actual = json.loads(source.read_text())
        for node in actual['nodes']:
            for credential in node.get('credentials', {}).values():
                credential['id'] = 'id-de-esta-instancia'
            if node['type'] == 'n8n-nodes-base.emailReadImap':
                node['credentials']['imap']['name'] = 'Buzón local del laboratorio'
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'workflow.json'
            output.write_text(json.dumps(declared))
            with patch.object(lab, 'request', return_value={'data': actual}):
                lab.export('workflow-local', output)
            exported = json.loads(output.read_text())
        expected = {node['name']: node.get('credentials', {}) for node in declared['nodes']}
        for node in exported['nodes']:
            self.assertEqual(node.get('credentials', {}), expected[node['name']])
        self.assertFalse(exported['active'])


if __name__ == '__main__':
    unittest.main(argv=['test_credenciales'], verbosity=2)
