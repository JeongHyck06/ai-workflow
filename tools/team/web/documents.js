'use strict';
(() => {
  const el=id=>document.getElementById(id);
  const dialog=el('docs-dialog');
  const markdown=window.markdownit({html:false,linkify:false,typographer:false}).disable('image');
  let docs=[], selected='docs/README.md', generation=0, opener=null;
  function renderList(){
    const filter=el('doc-search').value.trim().toLocaleLowerCase();
    const shown=docs.filter(d=>(d.title+' '+d.path+' '+d.group).toLocaleLowerCase().includes(filter));
    const fragment=document.createDocumentFragment();
    for(const group of [...new Set(shown.map(d=>d.group))]){
      const label=document.createElement('h3');label.textContent=group;fragment.append(label);
      for(const doc of shown.filter(d=>d.group===group)){
        const button=document.createElement('button');button.textContent=doc.title;button.title=doc.path;
        button.setAttribute('aria-current',String(doc.path===selected));button.addEventListener('click',()=>load(doc.path));fragment.append(button);
      }
    }
    el('doc-list').replaceChildren(fragment);el('doc-count').textContent=shown.length?`${shown.length}개 문서`:'일치하는 문서가 없습니다.';
  }
  async function load(path,anchor=''){
    const request=++generation;selected=path;renderList();
    el('doc-title').textContent=docs.find(d=>d.path===path)?.title||'문서';el('doc-path').textContent=path;el('doc-updated').textContent='불러오는 중…';el('doc-error').hidden=true;el('doc-content').replaceChildren();
    try{
      const r=await fetch('/api/doc?path='+encodeURIComponent(path),{cache:'no-store'});const result=await r.json();if(request!==generation)return;if(!r.ok)throw new Error(result.error);
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
    try{const r=await fetch('/api/docs',{cache:'no-store'});const result=await r.json();if(!r.ok)throw new Error(result.error);docs=result.documents;renderList();await load(path||selected);}
    catch(error){el('doc-error').hidden=false;el('doc-error').textContent=error.message||'문서 목록을 불러오지 못했습니다.';}
  }
  el('docs-open').addEventListener('click',()=>open());
  document.querySelectorAll('[data-doc]').forEach(button=>button.addEventListener('click',()=>open(button.dataset.doc)));
  el('docs-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{generation++;opener?.focus();});
  el('doc-search').addEventListener('input',renderList);
  el('doc-refresh').addEventListener('click',()=>load(selected));
})();
