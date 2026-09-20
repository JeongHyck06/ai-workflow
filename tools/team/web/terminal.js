'use strict';
(() => {
  const el=id=>document.getElementById(id);
  let connection=null, token=null, timer=null, connecting=false, queue=Promise.resolve();
  const term=new Terminal({fontSize:13,fontFamily:'Menlo, monospace',cursorBlink:true,scrollback:5000,theme:{background:'#101b2e',foreground:'#d8e3f5'},allowProposedApi:false});
  const fit=new FitAddon.FitAddon();term.loadAddon(fit);term.open(el('terminal'));
  const status=message=>{el('pm-connection').textContent=message;};
  async function post(path,body){
    if(!token){const r=await fetch('/api/session');token=(await r.json()).token;}
    const r=await fetch('/api/pm/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Team-Token':token},body:JSON.stringify(body),signal:AbortSignal.timeout(15000)});
    const result=await r.json();if(!r.ok)throw new Error(result.error||'연결 실패');return result;
  }
  function disconnected(message){clearTimeout(timer);const old=connection;connection=null;el('pm-input').disabled=true;el('pm-send').disabled=true;el('pm-connect').disabled=false;el('pm-connect').textContent='다시 연결';status(message);if(old)post('disconnect',{connection:old}).catch(()=>{});}
  function send(data){
    const target=connection;
    if(!target)return Promise.reject(new Error('PM에 먼저 연결하세요.'));
    const task=queue.then(()=>{if(connection!==target)throw new Error('연결이 변경됐습니다.');return post('input',{connection:target,data});});
    queue=task.catch(error=>disconnected(error.message+' 전송 여부를 확인한 뒤 다시 연결하세요.'));
    return task;
  }
  term.onData(data=>{if(connection)send(data).catch(()=>{});});
  term.onResize(({cols,rows})=>{if(connection)post('resize',{connection,cols,rows}).catch(error=>status(error.message));});
  function size(){if(!el('pm-chat').hidden && el('terminal').clientHeight>50)fit.fit();}
  new ResizeObserver(size).observe(el('terminal'));
  window.addEventListener('rolechange',size);
  async function poll(){
    const target=connection;if(!target)return;
    try{const r=await fetch('/api/pm/output?connection='+encodeURIComponent(target),{cache:'no-store',signal:AbortSignal.timeout(10000)});const result=await r.json();if(connection!==target)return;if(!r.ok)throw new Error(result.error);if(result.output){const bytes=Uint8Array.from(atob(result.output),c=>c.charCodeAt(0));term.write(bytes);}if(result.closed){disconnected('PM 연결이 종료됐습니다.');return;}timer=setTimeout(poll,250);}catch(error){disconnected(error.message||'PM 연결이 끊겼습니다.');}
  }
  el('pm-connect').addEventListener('click',async()=>{
    if(connecting||connection)return;connecting=true;token=null;el('pm-connect').disabled=true;status('PM에 연결 중…');
    try{const result=await post('connect',{});term.reset();connection=result.connection;size();await post('resize',{connection,cols:term.cols,rows:term.rows});el('pm-input').disabled=false;el('pm-send').disabled=false;status('PM 연결됨 · 대화 화면 안에서 스크롤하세요.');el('pm-connect').textContent='연결됨';poll();}catch(error){disconnected(error.message);}finally{connecting=false;}
  });
  el('composer').addEventListener('submit',async event=>{
    event.preventDefault();const value=el('pm-input').value;if(!value.trim()||!connection)return;
    if(/[\x00-\x08\x0b-\x1f\x7f]/.test(value)){el('send-status').textContent='제어 문자는 메시지에 포함할 수 없습니다.';return;}
    el('pm-send').disabled=true;
    try{await send('\x1b[200~'+value+'\x1b[201~');await new Promise(resolve=>setTimeout(resolve,100));await send('\r');el('pm-input').value='';el('send-status').textContent='PM 입력을 전달했습니다. 응답은 위 대화 화면에 표시됩니다.';}catch{el('send-status').textContent='전송 상태를 확인할 수 없습니다. 대화를 확인한 뒤 다시 시도하세요.';}finally{el('pm-send').disabled=!connection;}
  });
  el('pm-input').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();if(!el('pm-send').disabled)el('composer').requestSubmit();}});
})();
