'use strict';
(() => {
  const el=id=>document.getElementById(id);
  const dialog=el('docs-dialog');
  const markdown=window.markdownit({html:false,linkify:false,typographer:false}).disable('image');
  let revision='', original='', editing=false, saving=false;
  const dirty=()=>editing&&el('doc-editor').value!==original;
  function mode(on){editing=on;el('doc-editor').hidden=!on;el('doc-content').hidden=on;el('doc-save').hidden=!on;el('doc-cancel').hidden=!on;el('doc-edit').hidden=on;}
  let docs=[], selected='docs/README.md', generation=0, opener=null;
  let seen={}, seenKey='', checking=false;
  const unread=doc=>seen[doc.path]!==doc.revision;
  function persistSeen(){try{localStorage.setItem(seenKey,JSON.stringify(seen));}catch{}}
  function acceptIndex(result){
    const key='document-read:'+result.project;
    if(key!==seenKey){
      seenKey=key;seen={};let stored=null;
      try{stored=JSON.parse(localStorage.getItem(key));}catch{}
      if(stored&&typeof stored==='object'&&!Array.isArray(stored))seen=stored;
      else{for(const doc of result.documents)seen[doc.path]=doc.revision;persistSeen();}
    }
    docs=result.documents;renderList();
  }
  function markRead(path,version){
    seen[path]=version;persistSeen();
    const doc=docs.find(d=>d.path===path);if(doc)doc.revision=version;
    renderList();
  }
  async function checkUpdates(){
    if(checking||document.hidden)return;checking=true;
    try{const response=await fetch('/api/docs',{cache:'no-store',signal:AbortSignal.timeout(10000)});
      if(response.ok)acceptIndex(await response.json());
    }catch{}finally{checking=false;}
  }
  function renderList(){
    const count=docs.filter(unread).length;
    el('docs-open').classList.toggle('has-update',count>0);
    el('docs-open').setAttribute('aria-label',count?`프로젝트 문서 · 확인하지 않은 업데이트 ${count}개`:'프로젝트 문서');
    el('docs-open').title=count?`업데이트된 문서 ${count}개`:'프로젝트 문서';
    const filter=el('doc-search').value.trim().toLocaleLowerCase();
    const shown=docs.filter(d=>(d.title+' '+d.path+' '+d.group).toLocaleLowerCase().includes(filter));
    const fragment=document.createDocumentFragment();
    for(const group of [...new Set(shown.map(d=>d.group))]){
      const label=document.createElement('h3');label.textContent=group;fragment.append(label);
      for(const doc of shown.filter(d=>d.group===group)){
        const button=document.createElement('button');button.textContent=doc.title;button.title=doc.path;button.classList.toggle('has-update',unread(doc));
        if(unread(doc))button.setAttribute('aria-label',doc.title+' · 업데이트 있음');
        button.setAttribute('aria-current',String(doc.path===selected));button.addEventListener('click',()=>load(doc.path));fragment.append(button);
      }
    }
    el('doc-list').replaceChildren(fragment);el('doc-count').textContent=shown.length?`${shown.length}개 문서`:'일치하는 문서가 없습니다.';
  }
  async function load(path,anchor=''){
    if(saving)return;
    if(dirty()&&!confirm('저장하지 않은 변경을 버리고 이동할까요?'))return;
    mode(false);el('doc-edit').disabled=true;
    const request=++generation;selected=path;renderList();
    el('doc-title').textContent=docs.find(d=>d.path===path)?.title||'문서';el('doc-path').textContent=path;el('doc-updated').textContent='불러오는 중…';el('doc-error').hidden=true;el('doc-content').replaceChildren();
    try{
      const r=await fetch('/api/doc?path='+encodeURIComponent(path),{cache:'no-store'});const result=await r.json();if(request!==generation)return;if(!r.ok)throw new Error(result.error);
      markRead(path,result.revision);
      revision=result.revision;original=result.content;el('doc-editor').value=original;el('doc-edit').disabled=false;
      el('doc-content').innerHTML=markdown.render(result.content);
      el('doc-updated').textContent='파일 수정 '+new Date(result.updated*1000).toLocaleString('ko-KR');
      for(const h of el('doc-content').querySelectorAll('h1,h2,h3,h4,h5,h6'))h.id=h.textContent.toLowerCase().replace(/[^\p{L}\p{N}\s_-]/gu,'').replace(/\s/g,'-');
      for(const a of el('doc-content').querySelectorAll('a')){
        const raw=a.getAttribute('href');
        if(!raw)continue;
        if(/^https?:\/\//i.test(raw)){a.target='_blank';a.rel='noopener noreferrer';continue;}
        if(/^[a-z][a-z0-9+.-]*:/i.test(raw)){a.removeAttribute('href');continue;}
        const url=new URL(raw,'https://project-docs.invalid/'+path), target=decodeURIComponent(url.pathname.slice(1)), hash=decodeURIComponent(url.hash.slice(1));
        if(docs.some(d=>d.path===target)){a.href='#'+hash;a.addEventListener('click',event=>{event.preventDefault();if(target===selected){const h=[...el('doc-content').querySelectorAll('[id]')].find(n=>n.id===hash);if(h)h.scrollIntoView({block:'start'});else el('doc-content').scrollTop=0;}else load(target,hash);});}
        else{a.removeAttribute('href');a.title='문서 창에서 열 수 없는 경로입니다.';}
      }
      el('doc-content').scrollTop=0;
      if(anchor){const h=[...el('doc-content').querySelectorAll('[id]')].find(n=>n.id===anchor);if(h)h.scrollIntoView({block:'start'});}
    }catch(error){if(request!==generation)return;el('doc-error').hidden=false;el('doc-error').textContent=error.message||'문서를 불러오지 못했습니다.';el('doc-updated').textContent='조회 실패';}
  }
  async function open(path){
    opener=document.activeElement;if(!dialog.open)dialog.showModal();el('doc-search').value='';
    try{const r=await fetch('/api/docs',{cache:'no-store'});const result=await r.json();if(!r.ok)throw new Error(result.error);acceptIndex(result);await load(path||selected);}
    catch(error){el('doc-error').hidden=false;el('doc-error').textContent=error.message||'문서 목록을 불러오지 못했습니다.';}
  }
  setInterval(checkUpdates,5000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)checkUpdates();});
  checkUpdates();
  el('docs-open').addEventListener('click',()=>open());
  document.querySelectorAll('[data-doc]').forEach(button=>button.addEventListener('click',()=>open(button.dataset.doc)));
  function canClose(){return !saving&&(!dirty()||confirm('저장하지 않은 변경을 버리고 닫을까요?'));}
  el('docs-close').addEventListener('click',()=>{if(canClose()){mode(false);dialog.close();}});
  dialog.addEventListener('cancel',event=>{if(!canClose())event.preventDefault();else mode(false);});
  dialog.addEventListener('close',()=>{generation++;opener?.focus();});
  el('doc-search').addEventListener('input',renderList);
  el('doc-refresh').addEventListener('click',()=>load(selected));
  el('doc-edit').addEventListener('click',()=>{mode(true);el('doc-editor').focus();});
  el('doc-cancel').addEventListener('click',()=>{if(saving)return;if(!dirty()||confirm('편집 내용을 버릴까요?')){el('doc-editor').value=original;mode(false);}});
  window.addEventListener('beforeunload',event=>{if(dirty()){event.preventDefault();event.returnValue='';}});
  el('doc-save').addEventListener('click',async()=>{
    if(saving)return;saving=true;el('doc-save').disabled=true;el('doc-editor').readOnly=true;
    try{
      const session=await fetch('/api/session',{cache:'no-store'}).then(r=>r.json());
      const response=await fetch('/api/doc',{method:'POST',headers:{'Content-Type':'application/json','X-Team-Token':session.token},body:JSON.stringify({path:selected,content:el('doc-editor').value,revision})});
      const result=await response.json();if(!response.ok)throw Error(result.error);
      original=result.content;revision=result.revision;mode(false);saving=false;await load(selected);
      el('doc-updated').textContent='저장했습니다. '+new Date(result.updated*1000).toLocaleString('ko-KR');
    }catch(error){el('doc-error').hidden=false;el('doc-error').textContent=error.message;}
    finally{saving=false;el('doc-save').disabled=false;el('doc-editor').readOnly=false;}
  });
})();
