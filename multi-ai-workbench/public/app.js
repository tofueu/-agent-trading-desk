const $ = (s) => document.querySelector(s);
const promptBox = $('#prompt'), workspaceInput = $('#workspace'), taskList = $('#taskList'), dialog = $('#resultDialog');
const agentInfo = {
  gemini: { name: 'Gemini · Antigravity', icon: '✦', url: 'https://antigravity.google/' },
  perplexity: { name: 'Perplexity Pro', icon: '◉', url: 'https://www.perplexity.ai/' },
  grok: { name: 'SuperGrok · Grok Bot', icon: '𝕏', url: 'https://grok.com/' }
};
let taskCache = [], activeTask = null, onlyActive = false;
function esc(s='') { return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function notify(text) { const el=$('#toast');el.textContent=text;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800); }
function time(s) { return new Intl.DateTimeFormat('zh-TW',{hour:'2-digit',minute:'2-digit'}).format(new Date(s)); }
function stateText(s) { return ({queued:'排隊中',running:'正在處理',planned:'待交辦',handoff:'已交辦／待回覆',done:'完成',error:'需要處理',cancelled:'已取消'})[s]||s; }
function rootProgress(root, children) { const done=children.filter(t=>t.status==='done').length; return {done,total:children.length,percent:children.length?Math.round(done/children.length*100):0}; }

async function checkHealth() {
  try { const data=await fetch('/api/health').then(r=>r.json());const el=$('#gemStatus');el.innerHTML=data.cli.available?`<i class="status-dot"></i>${esc(data.cli.version)}`:'<i class="status-dot offline"></i>尚未連線';el.classList.toggle('offline',!data.cli.available);if(!workspaceInput.value)workspaceInput.placeholder=data.defaultWorkspace; }
  catch { $('#gemStatus').innerHTML='<i class="status-dot offline"></i>工作台離線'; }
}
function renderTasks() {
  const allRoots=taskCache.filter(t=>t.kind==='parent'||(!t.parentId&&t.kind!=='child'));
  const roots=onlyActive?allRoots.filter(root=>root.status!=='done'):allRoots;
  if(!roots.length){taskList.innerHTML='<div class="empty-state">目前沒有主任務。建立一個主目標，工作台就會展開分工樹。</div>';return;}
  taskList.innerHTML=roots.map(root=>{
    const children=taskCache.filter(t=>t.parentId===root.id);
    const p=rootProgress(root,children);
    const state=children.length&&children.every(c=>c.status==='done')?'done':root.status;
    const repo=root.repoUrl?`<a class="repo-link" href="${esc(root.repoUrl)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">⌘ GitHub Repository ↗</a>`:'';
    const issue=root.issueUrl?`<a class="repo-link" href="${esc(root.issueUrl)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Issue / PR ↗</a>`:'';
    const kids=children.map(child=>{
      const info=agentInfo[child.agent]||agentInfo.gemini;
      const action=child.status==='planned'?`<button class="tree-action" data-dispatch="${esc(child.id)}">交辦 ↗</button>`:child.status==='handoff'?`<button class="tree-action secondary" data-dispatch="${esc(child.id)}">重新開啟 ↗</button>`:`<button class="tree-action secondary" data-open="${esc(child.id)}">查看</button>`;
      return `<div class="tree-child"><div class="tree-branch"></div><div class="task-agent-icon ${esc(child.agent)}">${info.icon}</div><div class="tree-child-main"><div class="tree-role">${esc(child.role)}</div><div class="tree-assignee">${info.name}</div></div><span class="tree-state ${esc(child.status)}"><i></i>${stateText(child.status)}</span>${action}</div>`;
    }).join('');
    return `<article class="tree-root"><div class="tree-root-head"><div class="root-icon">▣</div><div class="root-main"><div class="root-title">${esc(root.projectName||root.prompt.slice(0,60))}</div><div class="root-objective">${esc(root.prompt)}</div><div class="repo-links">${repo}${issue}<span class="local-tag">📁 ${esc(root.workspace||'未設定工作資料夾')}</span></div></div><div class="root-progress"><strong>${p.done}/${p.total}</strong><small>子任務完成</small><div class="progress-track"><i style="width:${p.percent}%"></i></div></div><button class="collapse-btn" aria-label="收合">⌄</button></div><div class="tree-children">${kids||'<div class="empty-state">沒有子任務</div>'}</div></article>`;
  }).join('');
  taskList.querySelectorAll('[data-dispatch]').forEach(btn=>btn.addEventListener('click',e=>{e.stopPropagation();dispatchExternal(btn.dataset.dispatch);}));
  taskList.querySelectorAll('[data-open]').forEach(btn=>btn.addEventListener('click',e=>{e.stopPropagation();showTask(btn.dataset.open);}));
  taskList.querySelectorAll('.tree-root-head').forEach(head=>head.addEventListener('click',()=>head.parentElement.classList.toggle('collapsed')));
}
async function loadTasks(){try{taskCache=await fetch('/api/tasks').then(r=>r.json());renderTasks();}catch{taskList.innerHTML='<div class="empty-state">無法讀取任務記錄。</div>';}}

async function createTask() {
  const prompt=promptBox.value.trim(), workspace=workspaceInput.value.trim();
  if(!prompt)return notify('先輸入主任務內容。');
  if(!workspace)return notify('請輸入要處理的本機專案資料夾完整路徑。');
  const button=$('#runBtn');button.disabled=true;button.querySelector('span').textContent='建立分工中…';
  try{
    const body={agent:'gemini',mode:$('#mode').value,projectName:$('#projectName').value.trim(),repoUrl:$('#repoUrl').value.trim(),issueUrl:$('#issueUrl').value.trim(),prompt,workspace};
    const res=await fetch('/api/tasks',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)}),data=await res.json();
    if(!res.ok)throw new Error(data.error||'建立失敗');
    promptBox.value='';notify('主任務已建立，Gemini 開始實作；研究與審查任務已列入分工樹。');await loadTasks();
  }catch(e){notify(e.message);}finally{button.disabled=false;button.querySelector('span').textContent='建立分工';}
}
async function dispatchExternal(id){
  const task=taskCache.find(t=>t.id===id);if(!task)return;
  try{
    await fetch(`/api/tasks/${id}/dispatch`,{method:'POST'});
    const info=agentInfo[task.agent];await navigator.clipboard.writeText(task.prompt).catch(()=>{});window.open(info.url,'_blank','noopener');
    notify(`${info.name} 任務提示已複製；完成後到分工樹貼回結果。`);await loadTasks();
  }catch{notify('交辦失敗，請重新操作。');}
}
async function showTask(id){
  const task=taskCache.find(t=>t.id===id);if(!task)return;activeTask=task;
  $('#dialogTitle').textContent=task.role||task.projectName||'任務結果';
  $('#resultText').textContent=task.response||task.logs||task.prompt;
  $('#pasteArea').classList.toggle('hidden',task.agent==='gemini'||task.status==='done');$('#manualResult').value='';
  $('#copyPrompt').onclick=async()=>{await navigator.clipboard.writeText(task.prompt);notify('交辦內容已複製。');};dialog.showModal();
}
$('#saveResult').addEventListener('click',async()=>{if(!activeTask)return;const response=$('#manualResult').value.trim();if(!response)return notify('請先貼上 AI 回覆。');const res=await fetch(`/api/tasks/${activeTask.id}/result`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({response})});if(!res.ok)return notify('儲存回覆失敗。');dialog.close();notify('審查結果已存回任務分工樹。');loadTasks();});
$('#runBtn').addEventListener('click',createTask);
document.querySelectorAll('.mini-btn[data-agent]').forEach(btn=>btn.addEventListener('click',()=>{const p=btn.closest('.agent-card');promptBox.value=`請負責${p.querySelector('h3').textContent}的工作，針對目前主專案提供結果。`;promptBox.focus();notify('請補充主目標，再建立套娃分工。');}));
document.querySelectorAll('.project-link').forEach(btn=>btn.addEventListener('click',()=>{promptBox.value=btn.dataset.prompt;promptBox.focus();}));
$('#refreshBtn').addEventListener('click',()=>{checkHealth();loadTasks();notify('任務與連線狀態已更新。');});
$('#clearView').addEventListener('click',()=>{onlyActive=!onlyActive;$('#clearView').textContent=onlyActive?'顯示全部主任務':'只看進行中';renderTasks();});
$('#settingsBtn').addEventListener('click',()=>notify('權限設定與啟動方式請看 README。'));
workspaceInput.value=localStorage.getItem('pro-ai-workbench-workspace')||'';workspaceInput.addEventListener('change',()=>localStorage.setItem('pro-ai-workbench-workspace',workspaceInput.value.trim()));
checkHealth();loadTasks();setInterval(()=>{loadTasks();checkHealth();},3500);
