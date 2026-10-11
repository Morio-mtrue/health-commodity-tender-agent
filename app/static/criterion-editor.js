/* Human check configuration. Source quotations remain read-only and server-validated. */
function openCriterionEditor(index) {
  const original = current.plan.criteria[index];
  let dialog = $('#criterion-dialog');
  if (!dialog) {
    dialog = document.createElement('dialog');
    dialog.id = 'criterion-dialog';
    dialog.setAttribute('aria-labelledby', 'criterion-heading');
    document.body.append(dialog);
  }
  const evidence = new Map();
  for (const doc of current.documents.filter(d => d.kind === 'bid')) {
    const data = doc.extraction.structured || {};
    for (const [key, value] of Object.entries(data)) {
      if (key !== 'synthetic' && !Array.isArray(value)) evidence.set(key, key.replaceAll('_', ' '));
    }
    for (const product of data.products || []) {
      for (const key of Object.keys(product)) {
        if (key !== 'item_id') evidence.set('products.' + product.item_id + '.' + key, product.item_id + ' · ' + key.replaceAll('_', ' '));
      }
    }
  }
  if (original.field && original.field !== 'products') evidence.set(original.field, original.field.replaceAll('_', ' '));
  const methods = {manual:'Human interpretation required',present:'Required evidence is present',exact:'Submitted value matches published value',
    minimum:'Submitted value meets published minimum',expiry:'Registration is valid on closing date',arithmetic:'Price arithmetic and pack normalization'};
  let arithmetic = {};
  if (original.method === 'arithmetic') { try { arithmetic = JSON.parse(original.expected); } catch {} }
  dialog.innerHTML = `<div class="dialog-head"><h2 id="criterion-heading">Configure check · ${esc(original.id)}</h2><button type="button" id="close-criterion" class="secondary">Cancel</button></div>
    <p class="small muted">Choose only a check supported by this quotation. Saving creates a new draft revision and requires a new named plan approval.</p>
    <pre>${esc(original.source.quote)}</pre>
    <form id="criterion-form">
      <label for="check-method">How to check this requirement</label>
      <select id="check-method" autofocus>${Object.entries(methods).map(([key,label])=>`<option value="${key}" ${original.method===key?'selected':''}>${label}</option>`).join('')}</select>
      <div id="check-field-wrap"><label for="check-field">Submitted evidence to inspect</label>
        <select id="check-field"><option value="">Choose evidence</option>${[...evidence].sort((a,b)=>a[1].localeCompare(b[1])).map(([key,label])=>`<option value="${esc(key)}" ${original.field===key?'selected':''}>${esc(label)}</option>`).join('')}</select></div>
      <div id="check-value-wrap"><label for="check-value">Published value</label><input id="check-value" value="${esc(original.expected)}"><p class="small muted">Use the exact value from the quoted requirement. Enter a number for a minimum check.</p></div>
      <div id="check-price-wrap" class="form-grid">
        <div><label for="check-currency">Published currency</label><input id="check-currency" minlength="3" maxlength="3" pattern="[A-Z]{3}" value="${esc(arithmetic.currency || '')}" placeholder="KES"></div>
        <div><label for="check-rounding">Published rounding increment</label><input id="check-rounding" value="${esc(arithmetic.rounding || '')}" placeholder="0.01"></div>
      </div>
      <p class="small muted" id="check-manual-note">This requirement will remain unresolved until the committee interprets its evidence.</p>
      <button class="primary" type="submit">Save check as a new draft</button>
    </form>`;
  const update = () => {
    const method = $('#check-method').value;
    const fieldNeeded = ['present','exact','minimum','expiry'].includes(method);
    const valueNeeded = ['exact','minimum'].includes(method);
    const priceNeeded = method === 'arithmetic';
    $('#check-field-wrap').hidden = !fieldNeeded; $('#check-field').required = fieldNeeded;
    $('#check-value-wrap').hidden = !valueNeeded; $('#check-value').required = valueNeeded;
    $('#check-price-wrap').hidden = !priceNeeded;
    $('#check-currency').required = priceNeeded; $('#check-rounding').required = priceNeeded;
    $('#check-manual-note').hidden = method !== 'manual';
  };
  $('#check-method').onchange = update;
  $('#close-criterion').onclick = () => dialog.close();
  $('#criterion-form').onsubmit = event => {
    event.preventDefault();
    const criteria = structuredClone(current.plan.criteria);
    const changed = criteria[index];
    changed.method = $('#check-method').value;
    changed.field = changed.method === 'arithmetic' ? 'products' : changed.method === 'manual' ? '' : $('#check-field').value;
    changed.expected = changed.method === 'arithmetic' ? JSON.stringify({...arithmetic,currency:$('#check-currency').value,rounding:$('#check-rounding').value})
      : ['exact','minimum'].includes(changed.method) ? $('#check-value').value : '';
    dialog.close();
    action(async () => { await api(`/api/cases/${current.id}/plan/revise`,{criteria}); }, 'Checking the published source and saving a new plan revision…');
  };
  update();
  dialog.showModal();
}
