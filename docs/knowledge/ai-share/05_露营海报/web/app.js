const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let snapshot=null, visualKey='', saving=false;
const layoutText={hero:'大图主视觉',split:'图文分栏',cards:'参数卡片'};
const statusText={success:'已生成',building:'编译中',failed:'失败，保留旧版',pending:'等待更新'};
function time(v){return v?new Date(v).toLocaleString('zh-CN',{hour12:false}):'尚未生成'}
function render(data){
  snapshot=data;
  $('#worker').textContent=`本地服务运行中 · 每 ${data.interval} 秒检测变化 · 未连接钉钉`;
  if(data.error||data.status.error) $('#message').textContent=data.error||data.status.error;
  const states=Object.fromEntries(data.status.records.map(r=>[r.record_id,r]));
  // Do not replace a focused input or destroy a pending user edit during polling.
  const editing=$('#products').contains(document.activeElement);
  if(!editing&&!saving){
    $('#products').innerHTML=data.products.map(p=>{
      const s=states[p.record_id]||{};
      return `<tr><td><strong>${esc(p.product_name)}</strong><small>${esc(p.model_id)} / ${esc(p.record_id)}</small><small>${esc(layoutText[p.layout])}</small></td><td>${esc(p.capacity_wh)} Wh</td><td>${esc(p.rated_power_w)} W</td><td>${esc(p.weight_kg)} kg</td><td><form data-record="${esc(p.record_id)}" data-csv-hash="${esc(data.csv_hash)}"><input aria-label="${esc(p.product_name)} 教学价" name="price" value="${esc(p.price_cny)}" type="number" min="0.01" max="99999" step="0.01" required><button type="submit">保存</button></form></td><td><span class="status ${esc(s.status||'pending')}">${esc(statusText[s.status]||'等待生成')}</span>${s.pdf?` <a target="_blank" href="/${esc(s.pdf)}?v=${s.version}">PDF ↗</a><small>v${s.version} · SHA ${esc(s.pdf_sha256.slice(0,8))}</small>`:''}</td><td>${esc(time(s.updated_at))}<small>${esc(s.error||s.change_summary||'')}</small></td></tr>`;
    }).join('');
  }
  const nextKey=JSON.stringify(data.status.records.map(r=>[r.record_id,r.version,r.pdf_sha256]));
  if(nextKey!==visualKey){
    visualKey=nextKey;
    $('#posters').innerHTML=data.products.map(p=>{const s=states[p.record_id]||{};return `<article class="poster">${s.pdf?`<a href="/${esc(s.pdf)}?v=${s.version}" target="_blank"><img src="/output/previews/${esc(p.model_id)}.png?v=${s.version}" alt="${esc(p.product_name)} LaTeX PDF 实际预览"></a>`:'<div class="empty">等待首次编译…</div>'}<div class="caption"><strong>${esc(p.product_name)}</strong><span>${esc(layoutText[p.layout])} · ${s.version?'v'+s.version:'未生成'}</span></div></article>`}).join('');
  }
  const eventText={build_started:'开始编译',build_succeeded:'PDF 已更新',build_failed:'构建失败',data_saved:'CSV 数据已保存',input_error:'输入校验失败',worker_error:'后台错误',superseded:'数据再次变化，等待新一轮构建'};
  $('#events').innerHTML=[...data.events].reverse().map(e=>`<li><time>${esc(new Date(e.time).toLocaleTimeString('zh-CN',{hour12:false}))}</time><div><strong>${esc(eventText[e.event]||e.event)}</strong> ${esc(e.model_id||e.record_id||'')} ${e.version?'v'+e.version:''}<span class="detail">${esc(e.error||e.change_summary||(e.changed_fields||[]).join(', '))}</span>${e.pdf_sha256?`<code>PDF SHA-256: ${esc(e.pdf_sha256.slice(0,20))}…</code>`:''}</div></li>`).join('');
}
$('#products').addEventListener('submit',async event=>{
  event.preventDefault();const form=event.target;if(!snapshot)return;
  saving=true;const button=form.querySelector('button');button.disabled=true;
  try{
    const response=await fetch('/api/product',{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Token':snapshot.token},body:JSON.stringify({record_id:form.dataset.record,changes:{price_cny:form.elements.price.value},csv_hash:form.dataset.csvHash})});
    const result=await response.json();if(!response.ok)throw new Error(result.error);
    $('#message').textContent='已保存到 CSV。后台将自动检测并更新对应 PDF，无需再点生成。';
    document.activeElement.blur();
  }catch(e){$('#message').textContent=e.message}finally{saving=false;button.disabled=false;await refresh()}
});
async function refresh(){try{const r=await fetch('/api/state');if(!r.ok)throw new Error('本地服务不可用');render(await r.json())}catch(e){$('#worker').textContent='本地服务未运行。请启动“启动本地演示.command”。'}}
refresh();setInterval(refresh,1000);
