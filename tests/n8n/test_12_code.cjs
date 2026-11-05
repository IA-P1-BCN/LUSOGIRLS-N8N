const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const workflow = JSON.parse(fs.readFileSync(path.join(__dirname, '../../workflows/12-ventas-datafono.json')));
const header = 'terminal_id;operacion_id;fecha;tipo;concepto;importe;moneda;venta_id\n';
const context = {fecha:'2026-10-27', config:{}};
function execute(name, input, previous) {
  const code = workflow.nodes.find(n => n.name === name).parameters.jsCode;
  return new Function('$input', '$', code)(
    {first:()=>({json:input})}, name=>({first:()=>({json:previous[name]})})
  )[0].json;
}
function parse(lines) {
  return execute('Validar CSV del datáfono', {csv:header+lines}, {'Fijar día y fuente':context});
}
function plan(lote, ventas) {
  return execute('Planificar ventas sin duplicados',{body:ventas},{'Validar CSV del datáfono':lote});
}
const row = (id='A',extra={}) => ['TPV01',id,'2026-10-27','venta','Zapatos','39,90','EUR',''].map((v,i)=>Object.hasOwn(extra,i)?extra[i]:v).join(';')+'\n';

test('CSV quoted, decimal exacto, BOM, CRLF y dos cobros legítimos iguales',()=>{
  const lote = parse(row('A',{4:'"Zapatos; modelo ""azul"""'})+row('B'));
  assert.equal(lote.operaciones[0].documento.centimos,3990);
  assert.equal(lote.operaciones[0].documento.concepto,'Zapatos; modelo "azul"');
  assert.equal(plan(lote,[]).plan.length,2);
  const normalized=execute('Validar CSV del datáfono',{csv:'\uFEFF'+(header+row()).replaceAll('\n','\r\n')},{'Fijar día y fuente':context});
  assert.equal(normalized.operaciones.length,1);
});
test('La referencia sobrevive al orden de filas; repetición idéntica se procesa una vez',()=>{
  const lote=parse(row('A')+row('A')+row('B'));
  assert.equal(lote.duplicados,1);
  assert.deepEqual(lote.operaciones.map(o=>o.clave).sort(),parse(row('B')+row('A')).operaciones.map(o=>o.clave).sort());
});
test('Conflicto entre filas retiene toda la referencia, también si una es inválida',()=>{
  assert.equal(parse(row()+row('A',{5:'50,00'})).operaciones.length,0);
  assert.equal(parse(row()+row('A',{5:'-1'})).operaciones.length,0);
});
test('Abonos, devoluciones, otra moneda, fecha distinta e importes ambiguos no generan operaciones',()=>{
  for(const fields of [{3:'abono'},{3:'devolucion'},{6:'USD'},{2:'2026-10-26'},{5:'1.000,00'},{5:'1.842'},{5:'0'},{5:'NaN'},{7:'2x'}]) {
    const lote=parse(row('A',fields));assert.equal(lote.operaciones.length,0);assert.ok(lote.incidencias.length);
  }
});
test('CSV estructuralmente roto falla por completo y el vacío válido produce cero operaciones',()=>{
  assert.throws(()=>parse(row()+'TPV01;"sin cerrar'));
  assert.throws(()=>parse(row()+'TPV01;A\n'));
  assert.throws(()=>execute('Validar CSV del datáfono',{csv:'otra;cabecera\n'},{'Fijar día y fuente':context}));
  assert.equal(plan(parse(''),[]).plan.length,0);
});
test('Reconoce marcador y venta manual; retiene coincidencias ambiguas y vínculos incompatibles',()=>{
  const venta={id:7,fecha:context.fecha,forma_pago:'tarjeta',importe:39.9,concepto:'Zapatos'};
  assert.equal(plan(parse(row()),[venta]).plan.length,0);
  assert.equal(plan(parse(row('A',{7:'7'})),[venta]).plan[0].existente,7);
  assert.equal(plan(parse(row('A',{7:'7'})),[{...venta,importe:40}]).plan.length,0);
  const marked={...venta,concepto:'[TPV:TPV01:A] Zapatos'};
  assert.equal(plan(parse(row()),[marked]).plan[0].existente,7);
  assert.equal(plan(parse(row()),[{...marked,importe:40}]).plan.length,0);
  assert.equal(plan(parse(row()),[marked,{...marked,id:8}]).plan.length,0);
  assert.equal(plan(parse(row('A',{7:'7'})+row('B',{7:'7'})),[venta]).plan.length,0);
});
