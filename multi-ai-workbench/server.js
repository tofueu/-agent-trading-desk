import http from 'node:http';
import { spawn, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { randomUUID } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const execFileAsync = promisify(execFile);
const ROOT = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(ROOT, 'data');
const DATA_FILE = path.join(DATA_DIR, 'tasks.json');
const PORT = Number(process.env.PORT || 4173);
const HOST = '127.0.0.1';
const AGY = process.env.ANTIGRAVITY_CLI || 'agy';
const PUBLIC_DIR = path.join(ROOT, 'public');

mkdirSync(DATA_DIR, { recursive: true });
if (!existsSync(DATA_FILE)) writeFileSync(DATA_FILE, '[]', 'utf8');

function loadTasks() {
  try { return JSON.parse(readFileSync(DATA_FILE, 'utf8')); }
  catch { return []; }
}
function saveTasks(tasks) { writeFileSync(DATA_FILE, JSON.stringify(tasks, null, 2), 'utf8'); }
function json(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(body));
}
function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => {
      data += chunk;
      if (data.length > 1_000_000) { reject(new Error('Request too large')); req.destroy(); }
    });
    req.on('end', () => {
      try { resolve(JSON.parse(data || '{}')); } catch { reject(new Error('Invalid JSON')); }
    });
    req.on('error', reject);
  });
}
function addLog(taskId, chunk, stream = 'out') {
  const tasks = loadTasks();
  const task = tasks.find(item => item.id === taskId);
  if (!task) return;
  const message = String(chunk).slice(-8000);
  task.logs = (task.logs || '').concat(stream === 'err' ? `\n${message}` : message).slice(-30000);
  task.updatedAt = new Date().toISOString();
  saveTasks(tasks);
}
function updateTask(taskId, changes) {
  const tasks = loadTasks();
  const i = tasks.findIndex(item => item.id === taskId);
  if (i < 0) return;
  tasks[i] = { ...tasks[i], ...changes, updatedAt: new Date().toISOString() };
  saveTasks(tasks);
}
function validWorkspace(value) {
  if (typeof value !== 'string' || !path.isAbsolute(value)) return false;
  try { return statSync(value).isDirectory(); } catch { return false; }
}

async function checkAntigravity() {
  try {
    const { stdout } = await execFileAsync(AGY, ['--version'], { timeout: 5000, windowsHide: true });
    return { available: true, version: stdout.trim() || 'Antigravity CLI available' };
  } catch (error) {
    return { available: false, version: null, message: error.code === 'ENOENT' ? '找不到 agy；請在安裝 Antigravity CLI 並登入的電腦執行本 App。' : (error.stderr || error.message).trim() };
  }
}

function runGemini(task) {
  updateTask(task.id, { status: 'running', startedAt: new Date().toISOString(), logs: '啟動 Antigravity CLI…\n' });
  const args = ['-p', task.prompt, '--mode=accept-edits', '--output-format', 'json'];
  let stdout = '';
  let stderr = '';
  const child = spawn(AGY, args, {
    cwd: task.workspace,
    env: { ...process.env, NO_COLOR: '1' },
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
    shell: false
  });
  child.stdout.on('data', chunk => { stdout += chunk; addLog(task.id, chunk); });
  child.stderr.on('data', chunk => { stderr += chunk; addLog(task.id, chunk, 'err'); });
  child.on('error', error => updateTask(task.id, { status: 'error', error: error.message, finishedAt: new Date().toISOString() }));
  child.on('close', code => {
    const current = loadTasks().find(item => item.id === task.id);
    if (!current || current.status === 'error') return;
    let response = '';
    try { const parsed = JSON.parse(stdout); response = parsed.response || parsed.result || stdout; }
    catch { response = stdout.trim(); }
    updateTask(task.id, { status: code === 0 ? 'done' : 'error', exitCode: code, response, error: code === 0 ? '' : stderr.trim(), finishedAt: new Date().toISOString() });
  });
}

function sendFile(res, filePath) {
  const ext = path.extname(filePath);
  const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };
  res.writeHead(200, { 'content-type': types[ext] || 'application/octet-stream', 'cache-control': 'no-cache' });
  res.end(readFileSync(filePath));
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${HOST}:${PORT}`);
  if (req.method === 'GET' && url.pathname === '/api/health') {
    const cli = await checkAntigravity();
    return json(res, 200, { ok: true, cli, platform: os.platform(), defaultWorkspace: process.cwd() });
  }
  if (req.method === 'GET' && url.pathname === '/api/tasks') return json(res, 200, loadTasks().sort((a,b) => b.createdAt.localeCompare(a.createdAt)));
  if (req.method === 'POST' && url.pathname === '/api/tasks') {
    let body;
    try { body = await readBody(req); } catch (e) { return json(res, 400, { error: e.message }); }
    const { agent, prompt, workspace, mode, projectName, repoUrl, issueUrl } = body;
    if (!['gemini', 'perplexity', 'grok'].includes(agent)) return json(res, 400, { error: '請選擇有效的 AI 助理。' });
    if (typeof prompt !== 'string' || !prompt.trim()) return json(res, 400, { error: '請輸入任務內容。' });
    if ((mode === 'team' || agent === 'gemini') && !validWorkspace(workspace)) return json(res, 400, { error: 'Gemini 任務需要有效的絕對專案資料夾路徑。' });
    if (mode === 'team') {
      const rootId = randomUUID();
      const createdAt = new Date().toISOString();
      const context = `\n\n專案：${projectName || prompt.trim().slice(0, 36)}\nGitHub：${repoUrl || '尚未設定'}\nIssue/PR：${issueUrl || '尚未設定'}`;
      const rootTask = { id: rootId, kind: 'parent', role: '總控／專案管理', agent: 'manager', prompt: prompt.trim(), projectName: projectName || prompt.trim().slice(0, 36), repoUrl: repoUrl || '', issueUrl: issueUrl || '', workspace, status: 'running', response: '', logs: '', createdAt, updatedAt: createdAt };
      const children = [
        { id: randomUUID(), kind: 'child', parentId: rootId, role: '需求研究與資料查證', agent: 'perplexity', status: 'planned', prompt: `針對以下專案需求做研究與查證，列出可執行建議、風險和來源連結。\n\n需求：${prompt.trim()}${context}` },
        { id: randomUUID(), kind: 'child', parentId: rootId, role: '程式實作', agent: 'gemini', status: 'queued', prompt: `請在目前工作資料夾直接實作以下專案需求。檢查現有架構，保留既有功能，完成後摘要修改檔案及驗證結果。\n\n需求：${prompt.trim()}${context}` },
        { id: randomUUID(), kind: 'child', parentId: rootId, role: '獨立審查與找問題', agent: 'grok', status: 'planned', prompt: `請獨立審查以下需求與實作結果，找出缺漏、錯誤風險、測試不足處並提出具體修正建議。\n\n需求：${prompt.trim()}${context}` }
      ].map(child => ({ ...child, projectName: rootTask.projectName, repoUrl: rootTask.repoUrl, issueUrl: rootTask.issueUrl, workspace, response: '', logs: '', createdAt, updatedAt: createdAt }));
      const tasks = loadTasks(); tasks.push(rootTask, ...children); saveTasks(tasks);
      runGemini(children[1]);
      return json(res, 201, { ...rootTask, children });
    }
    const task = {
      id: randomUUID(), kind: 'standalone', agent, role: agent === 'gemini' ? '程式實作' : agent === 'perplexity' ? '研究與查證' : '獨立審查', prompt: prompt.trim(), workspace: workspace || '',
      status: agent === 'gemini' ? 'queued' : 'handoff', response: '', logs: '',
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString()
    };
    const tasks = loadTasks(); tasks.push(task); saveTasks(tasks);
    if (agent === 'gemini') runGemini(task);
    return json(res, 201, task);
  }
  const dispatchMatch = url.pathname.match(/^\/api\/tasks\/([\w-]+)\/dispatch$/);
  if (req.method === 'POST' && dispatchMatch) {
    const task = loadTasks().find(item => item.id === dispatchMatch[1]);
    if (!task) return json(res, 404, { error: '找不到任務。' });
    updateTask(task.id, { status: 'handoff', dispatchedAt: new Date().toISOString() });
    return json(res, 200, { ok: true, task: { ...task, status: 'handoff' } });
  }
  const resultMatch = url.pathname.match(/^\/api\/tasks\/([\w-]+)\/result$/);
  if (req.method === 'POST' && resultMatch) {
    let body;
    try { body = await readBody(req); } catch (e) { return json(res, 400, { error: e.message }); }
    if (typeof body.response !== 'string' || !body.response.trim()) return json(res, 400, { error: '請貼上 AI 回覆。' });
    const task = loadTasks().find(item => item.id === resultMatch[1]);
    if (!task) return json(res, 404, { error: '找不到任務。' });
    updateTask(task.id, { response: body.response.trim(), status: 'done', finishedAt: new Date().toISOString() });
    return json(res, 200, { ok: true });
  }
  const cancelMatch = url.pathname.match(/^\/api\/tasks\/([\w-]+)\/cancel$/);
  if (req.method === 'POST' && cancelMatch) {
    updateTask(cancelMatch[1], { status: 'cancelled', finishedAt: new Date().toISOString() });
    return json(res, 200, { ok: true });
  }
  const safePath = path.normalize(decodeURIComponent(url.pathname)).replace(/^([/\\])+/, '');
  const file = path.join(PUBLIC_DIR, safePath || 'index.html');
  if (!file.startsWith(PUBLIC_DIR) || !existsSync(file) || statSync(file).isDirectory()) return json(res, 404, { error: 'Not found' });
  sendFile(res, file);
});

server.listen(PORT, HOST, () => console.log(`AI Workbench is running at http://${HOST}:${PORT}`));
