'use strict';
const $ = id => document.getElementById(id);
const labels = {RUNNING:'실행 중', STOPPED:'종료', NOT_STARTED:'미시작', STARTING:'시작 중', UNKNOWN:'확인 불가'};
let data = null, selected = 'pm', busy = false;
const nodes = new Map();
function render() {
  if (!data) return;
  if(data.project){$('project-name').textContent='WORKSPACE / '+data.project.root;document.title='Team Monitor · '+data.project.name;}
  for (const role of data.roles) {
    let button = nodes.get(role.role);
    if (!button) {
      button = document.createElement('button'); button.className='role';
      const name=document.createElement('span'), dot=document.createElement('i'), title=document.createElement('span'), status=document.createElement('small');
      dot.className='dot'; name.append(dot,title); button.append(name,status);
      button.addEventListener('click',()=>{selected=role.role; render();});
      $('roles').append(button); nodes.set(role.role,button);
    }
    button.className='role '+role.status.toLowerCase();
    button.setAttribute('aria-pressed',String(selected===role.role));
    button.querySelector('span span').textContent=role.label;
    button.querySelector('small').textContent=labels[role.status] || role.status;
  }
  const role=data.roles.find(r=>r.role===selected);
  if (!role) return;
  $('role-title').textContent=role.label;
  $('meta').textContent=`${role.provider==='claude'?'Claude Code':'Codex'} / ${role.model}`;
  $('status').textContent=labels[role.status] || role.status;
  $('status').className='badge '+role.status.toLowerCase();
  const log=$('log'); const value=role.log || '표시할 출력이 없습니다.';
  if(log.textContent!==value){log.textContent=value;if($('follow').checked)log.scrollTop=log.scrollHeight;}
  $('message').textContent=role.message+(role.logUpdated?' 마지막 기록 '+new Date(role.logUpdated*1000).toLocaleString('ko-KR'):''); $('message').hidden=!role.message;
  const contactPM = role.role==='pm';
  $('pm-chat').hidden=!contactPM;
  $('view-mode').textContent=contactPM?'PM 대화':'최근 출력 · 읽기 전용';
  $('follow').closest('label').hidden=contactPM;
  $('log').hidden=contactPM;
  window.dispatchEvent(new Event('rolechange'));
  $('attach').textContent=contactPM?(role.session?`claude attach ${role.session}`:'PM 세션이 없습니다.'): '관찰 전용 · 요청과 질문은 PM에게 전달하세요.';
  $('copy').hidden=!contactPM;
  $('copy').disabled=!contactPM || !role.session;
  $('issues').textContent=data.issues;
  $('counts').textContent=`${data.roles.length}개 역할 · ${data.roles.filter(r=>r.status==='RUNNING').length}개 실행 중 · ${data.roles.filter(r=>r.status==='UNKNOWN').length}개 확인 불가`;
  $('updated').textContent='최근 확인 '+new Date(data.updated*1000).toLocaleTimeString('ko-KR');
}
async function refresh(){
  if(busy)return;busy=true;$('refresh').disabled=true;
  try{
    const response=await fetch('/api/state',{cache:'no-store',signal:AbortSignal.timeout(30000)});
    if(!response.ok)throw new Error('HTTP '+response.status);
    data=await response.json();render();
    $('error').hidden=!data.error;$('error').textContent=data.error||'';
    $('connection').textContent=data.error?'일부 조회 실패':'● 로컬 서버 연결됨';
  }catch(error){$('error').hidden=false;$('error').textContent='서버에 연결할 수 없습니다. 마지막 조회 결과를 표시합니다. 로컬 서버를 확인한 뒤 다시 시도하세요.';$('connection').textContent='연결 끊김';}
  finally{busy=false;$('refresh').disabled=false;}
}
$('refresh').addEventListener('click',refresh);
$('auto').addEventListener('change',()=>{if($('auto').checked)refresh();});
$('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('attach').textContent);$('copy').textContent='복사됨';}catch{$('copy').textContent='직접 복사해주세요';}setTimeout(()=>{$('copy').textContent='명령 복사';},1800);});
setInterval(()=>{if($('auto').checked && !document.hidden)refresh();},5000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden && $('auto').checked)refresh();});
refresh();
