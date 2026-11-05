def test_transferencia_liquida_sin_falsear_medio(cliente):
    nuevo=cliente.post('/api/apartados',json={'cliente':'Cliente prueba','producto':'Mocasín prueba','precio':17,'abono_inicial':5,'forma_pago':'efectivo'})
    assert nuevo.status_code==201
    ident=nuevo.json()['id']
    pago=cliente.post(f'/api/apartados/{ident}/abonos',json={'importe':12,'forma_pago':'transferencia'})
    assert pago.status_code==201 and pago.json()['estado']=='liquidado'
    detalle=cliente.get(f'/api/apartados/{ident}').json()
    assert detalle['pendiente']==0 and detalle['abonos'][-1]['forma_pago']=='transferencia'
    assert detalle['abonos'][-1]['importe']==12

def test_transferencia_respeta_limite(cliente):
    nuevo=cliente.post('/api/apartados',json={'cliente':'Cliente prueba','producto':'Mocasín prueba','precio':17,'abono_inicial':5})
    ident=nuevo.json()['id']
    assert cliente.post(f'/api/apartados/{ident}/abonos',json={'importe':13,'forma_pago':'transferencia'}).status_code==422
    assert len(cliente.get(f'/api/apartados/{ident}').json()['abonos'])==1
