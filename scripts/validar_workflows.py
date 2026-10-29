"""Validación estática de exportaciones; no ejecuta nodos ni consulta servicios."""
from pathlib import Path
import json
import subprocess
import sys


def validate(path):
    flow = json.loads(path.read_text())
    assert isinstance(flow, dict), 'la raíz debe ser un objeto'
    assert isinstance(flow.get('name'), str) and flow['name'].strip(), 'falta nombre'
    assert isinstance(flow.get('settings'), dict), 'falta settings'
    assert flow.get('active') is False, 'la exportación debe estar inactiva'
    assert flow.get('pinData') == {}, 'la exportación debe estar sin datos fijados'
    nodes = flow.get('nodes')
    assert isinstance(nodes, list) and nodes, 'faltan nodos'
    names, identifiers, scripts = set(), set(), []
    for node in nodes:
        name, identifier = node.get('name'), node.get('id')
        assert isinstance(name, str) and name.strip() and name not in names, 'nombre de nodo ausente o repetido'
        assert isinstance(identifier, str) and identifier and identifier not in identifiers, 'id de nodo ausente o repetido'
        names.add(name); identifiers.add(identifier)
        assert isinstance(node.get('type'), str) and node['type'], 'tipo de nodo ausente'
        assert isinstance(node.get('parameters'), dict), 'parámetros ausentes'
        for credential in node.get('credentials', {}).values():
            assert isinstance(credential, dict) and set(credential) == {'name'}, 'credencial con ID local o valores incrustados'
            assert isinstance(credential['name'], str) and credential['name'].strip(), 'credencial sin nombre'
        if node['type'] == 'n8n-nodes-base.code':
            code = node['parameters'].get('jsCode')
            assert isinstance(code, str), 'Code node sin JavaScript'
            scripts.append(code)
    connections = flow.get('connections')
    assert isinstance(connections, dict), 'faltan conexiones'
    for source, outputs in connections.items():
        assert source in names and isinstance(outputs, dict), 'origen de conexión inexistente'
        for kind, branches in outputs.items():
            assert isinstance(branches, list), 'salidas inválidas'
            for branch in branches:
                assert isinstance(branch, list), 'rama inválida'
                for edge in branch:
                    assert edge.get('node') in names, 'destino de conexión inexistente'
                    assert edge.get('type') == kind and isinstance(edge.get('index'), int) and edge['index'] >= 0, 'tipo/índice de conexión inválido'
    # Compilar no ejecuta las cadenas del workflow. El programa de Node es fijo.
    program = "const fs=require('node:fs');const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;for(const code of JSON.parse(fs.readFileSync(0,'utf8')))new AsyncFunction(code);"
    result = subprocess.run(['node', '-e', program], input=json.dumps(scripts), text=True, capture_output=True)
    assert result.returncode == 0, 'JavaScript de Code node no compila'
    return len(nodes), len(scripts)


def main():
    paths = [Path(p) for p in sys.argv[1:]] or sorted((Path(__file__).resolve().parents[1]/'workflows').glob('*.json'))
    if not paths:raise SystemExit('No hay workflows para validar')
    failures = 0
    for path in paths:
        try:
            nodes, scripts = validate(path)
            print(f'OK {path.name}: {nodes} nodos, {scripts} Code nodes')
        except (AssertionError, ValueError, TypeError, KeyError, OSError) as error:
            failures += 1
            print(f'ERROR {path.name}: {error}', file=sys.stderr)
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':main()
