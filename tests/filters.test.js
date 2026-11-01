const test=require('node:test');
const assert=require('node:assert/strict');
const {cents,filterRows}=require('../static/filters.js');
const rows=[
 {date:'2025-11-16',description:'Parcela antiga',cents:3500,category:'Casa',statement_month:'2026-10'},
 {date:'2026-09-01',description:'Mercado',cents:123456,category:'Mercado',statement_month:'2026-10'},
 {date:'2026-09-30',description:'Estorno',cents:-2000,category:'Casa',statement_month:null},
 {date:'2026-10-01',description:'Cinema',cents:5000,category:'Lazer',statement_month:'2026-11'}
];
test('valores brasileiros e estornos',()=>{assert.equal(cents('1.234,56'),123456);assert.equal(cents('-20,00'),-2000);assert.equal(cents(''),null);assert.throws(()=>cents('abc'));});
test('filtros combinados e limites inclusivos',()=>{assert.deepEqual(filterRows(rows,{month:'2026-10',from:'2026-09-01',to:'2026-09-30',min:'1.234,56',max:'1.234,56',search:'merc',category:'Mercado'}).map(r=>r.description),['Mercado']);});
test('mês da fatura não usa a data da parcela',()=>{assert.equal(filterRows(rows,{month:'2026-10'}).length,2);assert.equal(filterRows(rows,{month:'unassigned'})[0].description,'Estorno');});
test('ordenação numérica e faixas inválidas',()=>{assert.equal(filterRows(rows,{sort:'amount-asc'})[0].cents,-2000);assert.equal(filterRows(rows,{sort:'amount-desc'})[0].cents,123456);assert.throws(()=>filterRows(rows,{min:'30',max:'20'}));assert.throws(()=>filterRows(rows,{from:'2026-10-01',to:'2026-09-01'}));});
const {calendar}=require('../static/filters.js');
test('calendário soma por data, separa outros meses e ignora estornos',()=>{
 const c=calendar([{date:'2026-09-01',cents:100},{date:'2026-09-01',cents:250},{date:'2026-09-02',cents:-50},{date:'2026-08-01',cents:700}], '2026-09');
 assert.equal(c.days.length,30);assert.equal(c.offset,2);assert.equal(c.days[0],350);assert.equal(c.days[1],0);assert.equal(c.max,350);assert.equal(c.outside,700);
});
test('calendário respeita fevereiro bissexto e mês vazio',()=>{
 assert.equal(calendar([],'2024-02').days.length,29);assert.equal(calendar([],'2026-02').days.length,28);assert.equal(calendar([],'2026-12').max,0);assert.equal(calendar([],'2026-13'),null);
});
