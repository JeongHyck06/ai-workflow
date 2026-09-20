'use strict';
(() => {
  const el=id=>document.getElementById(id), dialog=el('resources-dialog');
  let generation=0, opener=null, active='links', hideTimer=null, ready=false;
  const status=text=>{el('resource-status').textContent=text;};
  async function api(path,body){
    const options={cache:'no-store',signal:AbortSignal.timeout(20000)};
    if(body){const session=await fetch('/api/session',{cache:'no-store'}).then(r=>r.json());Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json','X-Team-Token':session.token},body:JSON.stringify(body)});}
    const response=await fetch(path,options), data=await response.json();
    if(!response.ok)throw new Error(data.error||'요청을 처리하지 못했습니다.');
    return data;
  }
  function button(text,run){const b=document.createElement('button');b.type='button';b.textContent=text;b.addEventListener('click',run);return b;}
  function mask(){clearTimeout(hideTimer);for(const input of dialog.querySelectorAll('.secret-revealed'))input.remove();for(const b of dialog.querySelectorAll('[data-reveal]'))b.textContent='표시';}
  async function load(){
    const version=generation, data=await api('/api/resources');if(version!==generation)return;
    el('resource-project').textContent=data.name+' · '+data.root;
    for(const key of ['git','figma','deploy'])el('url-'+key).value=data.links[key]||'';
    updateLinks();renderSecrets(data.secrets);ready=true;
  }
  function updateLinks(){for(const key of ['git','figma','deploy']){const a=el('open-'+key),value=el('url-'+key).value;try{const u=new URL(value);if(!['http:','https:'].includes(u.protocol)||u.username||u.password)throw Error();a.href=u.href;a.hidden=false;}catch{a.removeAttribute('href');a.hidden=true;}}}
  function renderSecrets(items){
    mask();el('secret-list').replaceChildren();
    if(!items.length){const p=document.createElement('p');p.className='resource-empty';p.textContent='등록된 시크릿 키가 없습니다.';el('secret-list').append(p);}
    for(const item of items){
      const row=document.createElement('div');row.className='secret-row';
      const name=document.createElement('code');name.textContent=item.name;
      const hidden=document.createElement('span');hidden.textContent=item.masked;hidden.className='masked';
      const controls=document.createElement('div');controls.className='secret-controls';
      const reveal=button('표시',async()=>{
        if(row.querySelector('.secret-revealed')){mask();return;}mask();const version=generation;reveal.disabled=true;
        try{const result=await api('/api/resources',{action:'reveal-secret',name:item.name});if(version!==generation||active!=='secrets')return;const value=document.createElement('input');value.className='secret-revealed';value.readOnly=true;value.value=result.value;value.setAttribute('aria-label',item.name+' 값');row.append(value);reveal.textContent='숨기기';hideTimer=setTimeout(mask,30000);}catch(error){status(error.message);}finally{reveal.disabled=false;}
      });reveal.dataset.reveal='true';
      controls.append(reveal,button('수정',()=>{mask();el('secret-name').value=item.name;el('secret-value').value='';el('secret-value').focus();status('새 값을 입력하면 이 키를 교체합니다.');}),button('삭제',async()=>{const version=generation;try{await api('/api/resources',{action:'delete-secret',name:item.name});if(version!==generation)return;await load();status('키를 삭제했습니다.');}catch(error){status(error.message);}}));
      row.append(name,hidden,controls);el('secret-list').append(row);
    }
  }
  async function loadUsage(){
    const version=generation;el('usage-refresh').disabled=true;el('usage-scope').textContent='로컬 사용 기록을 조회하고 있습니다…';
    try{const data=await api('/api/usage');if(version!==generation)return;el('usage-scope').textContent=data.scope;el('usage-note').textContent=data.note;el('usage-updated').textContent='집계 '+new Date(data.updated*1000).toLocaleString('ko-KR')+' · 최대 30초 캐시';el('usage-cards').replaceChildren();
      for(const item of data.providers){const card=document.createElement('div');card.className='usage-card';const title=document.createElement('h3');title.textContent=item.provider;card.append(title);if(!item.available){const p=document.createElement('p');p.textContent=item.partial?'기록을 조회할 수 없습니다.':'사용량이 기록된 세션이 없습니다.';card.append(p);}else{const total=document.createElement('strong');total.textContent=(item.input+item.output).toLocaleString('ko-KR')+' tokens';card.append(total);const dl=document.createElement('dl');for(const [label,value] of [['입력 (캐시 포함)',item.input],['출력',item.output],['캐시 읽기 (입력 중)',item.cached],['집계 세션',item.sessions]]){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value.toLocaleString('ko-KR');dl.append(dt,dd);}card.append(dl);if(item.partial){const p=document.createElement('p');p.textContent='일부 기록을 읽지 못해 집계에서 제외했습니다.';card.append(p);}}el('usage-cards').append(card);}
    }catch(error){if(version===generation)el('usage-scope').textContent=error.message;}finally{el('usage-refresh').disabled=false;}
  }
  function select(name){active=name;mask();el('secret-value').value='';status('');for(const b of dialog.querySelectorAll('[data-resource-tab]')){const on=b.dataset.resourceTab===name;b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;el('panel-'+b.dataset.resourceTab).hidden=!on;}if(name==='usage')loadUsage();}
  for(const [key,label,placeholder] of [['git','Git 저장소','https://github.com/…'],['figma','Figma 디자인','https://www.figma.com/design/…'],['deploy','배포 URL (선택)','https://…']]){const row=document.createElement('div');row.className='url-field';const l=document.createElement('label');l.htmlFor='url-'+key;l.textContent=label;const input=document.createElement('input');input.id='url-'+key;input.type='url';input.placeholder=placeholder;input.maxLength=2000;input.addEventListener('input',updateLinks);const a=document.createElement('a');a.id='open-'+key;a.textContent='열기 ↗';a.target='_blank';a.rel='noopener noreferrer';a.hidden=true;row.append(l,input,a);el('link-fields').append(row);}
  for(const b of document.querySelectorAll('[data-resources]'))b.addEventListener('click',async()=>{opener=document.activeElement;generation++;ready=false;dialog.showModal();select(b.dataset.resources);try{await load();}catch(error){status(error.message);}});
  const tabs=[...dialog.querySelectorAll('[data-resource-tab]')];
  tabs.forEach((b,i)=>{b.addEventListener('click',()=>select(b.dataset.resourceTab));b.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const n=event.key==='Home'?0:event.key==='End'?tabs.length-1:(i+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[n].focus();select(tabs[n].dataset.resourceTab);});});
  el('resources-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{generation++;mask();el('secret-form').reset();el('secret-list').replaceChildren();opener?.focus();});
  el('secret-reset').addEventListener('click',()=>{mask();el('secret-form').reset();status('');});
  el('usage-refresh').addEventListener('click',loadUsage);
  for(const [form,body] of [['links-form',()=>({action:'links',links:Object.fromEntries(['git','figma','deploy'].map(k=>[k,el('url-'+k).value.trim()]))})],['secret-form',()=>({action:'save-secret',name:el('secret-name').value.trim(),value:el('secret-value').value})]])el(form).addEventListener('submit',async event=>{
    event.preventDefault();if(!ready){status('설정을 먼저 불러와야 합니다. 창을 다시 열어주세요.');return;}const submit=event.submitter;submit.disabled=true;const version=generation;
    try{await api('/api/resources',body());if(version!==generation)return;if(form==='secret-form')el(form).reset();await load();status('저장했습니다.');}catch(error){if(version===generation)status(error.message);}finally{submit.disabled=false;}
  });
})();
