const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.join(__dirname,'../..');
const flow=file=>JSON.parse(fs.readFileSync(path.join(root,'workflows',file+'.json')));
const c={CORREO_MARISA:'marisa@example.test',CORREO_REMITENTE:'tienda@example.test'};
const a={id:1,cliente:'Cliente ficticio',producto:'Zapatos',talla:'38',precio:60,abonado:10,pendiente:50,fecha_limite:'2026-11-04',estado:'activo',email:'cliente@example.test',consentimiento_notificaciones:true,importe:10};
function run(file,name,input,previous={}){
  const n=flow(file).nodes.find(n=>n.name===name);
  const items=Array.isArray(input)?input:[input];
  return new Function('$input','$json','$',n.parameters.jsCode)(
    {first:()=>({json:items[0]}),all:()=>items.map(json=>({json}))},items[0],
    k=>({first:()=>({json:previous[k]}),item:{json:previous[k]}}));
}
test('PF-01 y PF-02 solo preparan correo de cliente con true explícito',()=>{
  for(const [file,n,event] of [['01-confirmacion-apartado','Validar apartado','apartado.creado'],['02-recibo-abono','Validar abono','abono.registrado']]){
    for(const value of [true,false,undefined,1,'true']){
      const result=run(file,n,{config:c,entrada:{body:{evento:event,datos:{...a,consentimiento_notificaciones:value}}}})[0].json;
      assert.equal(result.documento.destino,value===true?'cliente':'tienda');
      assert.equal(result.documento.destinatario,value===true?a.email:c.CORREO_MARISA);
    }
  }
});
test('PF-06 protege recordatorios y vales; conserva el aviso a Marisa',()=>{
  for(const consent of [true,false,undefined]){
    const apartado={...a,consentimiento_notificaciones:consent};
    const recordatorios=run('06-recordatorios-vencimientos','Preparar recordatorio',{apartado,hito:7,config:c});
    assert.equal(recordatorios[0].json.documento.destino,consent===true?'cliente':'tienda');
    assert.equal(recordatorios[0].json.documento.apartado_id,a.id);
    const vales=run('06-recordatorios-vencimientos','Preparar avisos de vencimiento',{config:c,apartado:{...apartado,estado:'vencido'},vale:{apartado_id:1,codigo:'VALE-00001',importe:10}});
    assert.equal(vales.filter(i=>i.json.documento.destino==='cliente').length,consent===true?1:0);
    assert.equal(vales.filter(i=>i.json.documento.destino==='tienda').length,1);
    assert.ok(vales.every(i=>i.json.documento.apartado_id===1));
  }
});
test('Permiso revocado después del evento cambia el aviso a tienda; respuesta inválida falla cerrada',()=>{
  const original={clave:'evento:1',documento:{apartado_id:1,destino:'cliente',destinatario:a.email,texto:'Mensaje privado'}};
  const previous={'Preparar comprobación de consentimiento':original,'Leer configuración':{config:c}};
  for(const file of ['01-confirmacion-apartado','02-recibo-abono','06-recordatorios-vencimientos']){
    const result=run(file,'Aplicar consentimiento actual',{apartado_id:1,consentimiento_notificaciones:false},previous).json;
    assert.equal(result.documento.destinatario,c.CORREO_MARISA);
    assert.equal(result.documento.destino,'tienda');
    assert.ok(!result.documento.texto.includes('Mensaje privado'));
    assert.throws(()=>run(file,'Aplicar consentimiento actual',{apartado_id:2,consentimiento_notificaciones:true},previous));
    assert.throws(()=>run(file,'Aplicar consentimiento actual',{apartado_id:1,consentimiento_notificaciones:1},previous));
  }
});
test('PF-03 solo envía el contenido necesario y omite contacto, cuenta, enlaces y metadatos',()=>{
  const source={subject:'Has recibido un Bizum de 10,00 €',text:'Has recibido un Bizum.\nOrdenante: PERSONA FICTICIA\nImporte: 10,00 EUR\nConcepto: apartado 3, cliente@example.test, +34 612 345 678, ES9121000418450200051332, https://privado.example/cuenta\nSaldo: 12345 EUR\nTeléfono: +34 699 888 777',id:'privado-correo-id',clientes:[{nombre:'No enviar'}]};
  const request=run('03-abonos-distancia','Preparar petición IA',source)[0].json.peticion_ia;
  const outbound=JSON.stringify(request);
  for(const secret of ['cliente@example.test','612 345 678','ES9121000418450200051332','https://privado.example','12345','699 888 777','privado-correo-id','No enviar'])assert.ok(!outbound.includes(secret),secret);
  assert.ok(outbound.includes('PERSONA FICTICIA')&&outbound.includes('apartado 3')&&outbound.includes('10,00 EUR'));
  assert.equal(request.provider.max_price.prompt,0);assert.equal(request.provider.max_price.completion,0);
});
test('Negaciones y cambios de formato no se convierten en un aviso de pago recibido',()=>{
  const source={subject:'Transferencia no recibida',text:'Ordenante: PERSONA FICTICIA\nImporte: 10,00 EUR\nConcepto: zapatos'};
  assert.throws(()=>run('03-abonos-distancia','Preparar petición IA',source));
});
test('Los dos webhooks entregables exigen la credencial de cabecera y no llevan valores',()=>{
  for(const file of ['00-entrada-eventos','09-migracion']){
    const webhooks=flow(file).nodes.filter(n=>n.type.endsWith('.webhook'));
    assert.ok(webhooks.length);
    for(const n of webhooks){assert.equal(n.parameters.authentication,'headerAuth');assert.deepEqual(n.credentials.httpHeaderAuth,{name:'PF · Webhook tienda'});}
  }
});
