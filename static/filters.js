(function(root){
  function cents(value){
    let text=String(value??'').trim().replace(/R\$/g,'').replace(/\s/g,'');
    if(!text)return null;
    if(text.includes(',')){
      if(!/^-?(?:\d+|\d{1,3}(?:\.\d{3})+),\d{1,2}$/.test(text)&&!/^\-?\d+,$/.test(text))throw Error('Use valores como 50,00 ou 1.250,90.');
      text=text.replaceAll('.','').replace(',','.');
    }
    if(!/^-?\d+(?:\.\d{0,2})?$/.test(text))throw Error('Use valores como 50,00 ou 1.250,90.');
    const result=Math.round(Number(text)*100);
    if(!Number.isSafeInteger(result))throw Error('Valor fora do limite.');
    return result;
  }
  function filterRows(rows, f){
    const min=cents(f.min),max=cents(f.max);
    if(f.from&&f.to&&f.from>f.to)throw Error('A data inicial deve ser anterior ou igual à data final.');
    if(min!==null&&max!==null&&min>max)throw Error('O valor mínimo deve ser menor ou igual ao máximo.');
    const query=(f.search||'').toLocaleLowerCase();
    const result=rows.filter(r=>(!f.category||r.category===f.category)&&(!f.month||(f.month==='unassigned'?!r.statement_month:r.statement_month===f.month))&&(!f.from||r.date>=f.from)&&(!f.to||r.date<=f.to)&&(min===null||r.cents>=min)&&(max===null||r.cents<=max)&&r.description.toLocaleLowerCase().includes(query));
    const sort={
      'date-desc':(a,b)=>b.date.localeCompare(a.date),
      'date-asc':(a,b)=>a.date.localeCompare(b.date),
      'amount-desc':(a,b)=>b.cents-a.cents,
      'amount-asc':(a,b)=>a.cents-b.cents,
      'description':(a,b)=>a.description.localeCompare(b.description,'pt-BR')
    }[f.sort]||((a,b)=>b.date.localeCompare(a.date));
    return result.sort(sort);
  }
  const api={cents,filterRows};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.PocketFilters=api;
})(typeof globalThis!=='undefined'?globalThis:this);
