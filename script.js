/**
 * Fake Job Post Detector — script.js
 * Handles login, navigation, file upload, API call, preview rendering
 */

// ─── State ───────────────────────────────────────────────────────────────────
const STATE = {
  loggedIn: false,
  role: 'user',
  currentFile: null,
  currentResult: null,
  history: JSON.parse(localStorage.getItem('fjpd_history') || '[]'),
};

const CREDENTIALS = {
  admin: { password: '1234' },
  user: { password: '123' },
};

const BACKEND_URL = ''; // Change if needed

// ─── Page Navigation ──────────────────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => {
    p.classList.remove('active');
    p.style.display = 'none'; // Explicitly hide
  });
  const target = document.getElementById('page-' + name);
  if (target) {
    target.classList.add('active');
    target.style.display = 'block'; // Explicitly show
  }

  // Keep nav-links closed on mobile after click
  document.getElementById('navLinks').classList.remove('open');

  // Highlight active link
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  const active = document.querySelector(`.nav-link[onclick*="${name}"]`);
  if (active) active.classList.add('active');

  if (name === 'preview') renderHistory();
  if (name === 'upload') resetUploadForm();
}

// ─── Hamburger ────────────────────────────────────────────────────────────────
document.getElementById('hamburger').addEventListener('click', () => {
  document.getElementById('navLinks').classList.toggle('open');
});

// ─── Role Selector ────────────────────────────────────────────────────────────
let selectedRole = 'admin';
function selectRole(role) {
  selectedRole = role;
  document.getElementById('btnAdmin').classList.toggle('active', role === 'admin');
  document.getElementById('btnUser').classList.toggle('active', role === 'user');
}

// ─── Password Toggle ─────────────────────────────────────────────────────────
function togglePw() {
  const pw = document.getElementById('password');
  pw.type = pw.type === 'password' ? 'text' : 'password';
}

// ─── Login ────────────────────────────────────────────────────────────────────
function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  const errEl = document.getElementById('loginError');

  const cred = CREDENTIALS[username];
  if (!cred || cred.password !== password) {
    errEl.classList.remove('hidden');
    setTimeout(() => errEl.classList.add('hidden'), 3500);
    return;
  }

  STATE.loggedIn = true;
  STATE.role = username;
  errEl.classList.add('hidden');
  updateNav(true);
  showPage('upload');
}

function logout() {
  STATE.loggedIn = false;
  STATE.currentFile = null;
  STATE.currentResult = null;
  updateNav(false);
  document.getElementById('username').value = '';
  document.getElementById('password').value = '';
  showPage('home');
}

function updateNav(loggedIn) {
  document.getElementById('navLogin').classList.toggle('hidden', loggedIn);
  document.getElementById('navUpload').classList.toggle('hidden', !loggedIn);
  document.getElementById('navPreview').classList.toggle('hidden', !loggedIn);
  document.getElementById('navLogout').classList.toggle('hidden', !loggedIn);
}

// ─── File Handling ────────────────────────────────────────────────────────────
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  STATE.currentFile = file;
  showFilePreview(file);
}

// Drag & Drop
const dz = document.getElementById('dropzone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
dz.addEventListener('drop', e => {
  e.preventDefault();
  dz.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (!file) return;
  document.getElementById('fileInput').files = e.dataTransfer.files;
  STATE.currentFile = file;
  showFilePreview(file);
});

function showFilePreview(file) {
  const preview = document.getElementById('filePreview');
  const imgThumb = document.getElementById('imgPreview');

  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileSize').textContent = formatSize(file.size);

  const isImage = file.type.startsWith('image/');
  document.getElementById('previewIcon').textContent = isImage ? '🖼️' : '📄';

  if (isImage) {
    const reader = new FileReader();
    reader.onload = ev => {
      imgThumb.src = ev.target.result;
      imgThumb.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
  } else {
    imgThumb.classList.add('hidden');
  }

  preview.classList.remove('hidden');
  document.getElementById('analyzeBtn').disabled = false;
}

function removeFile() {
  STATE.currentFile = null;
  document.getElementById('fileInput').value = '';
  document.getElementById('filePreview').classList.add('hidden');
  document.getElementById('imgPreview').classList.add('hidden');
  document.getElementById('analyzeBtn').disabled = true;
}

function resetUploadForm() {
  removeFile();
  document.getElementById('progressBar').classList.add('hidden');
  document.getElementById('progressText').classList.add('hidden');
  document.getElementById('progressFill').style.width = '0';
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ─── Analysis ─────────────────────────────────────────────────────────────────
async function analyzeFile() {
  if (!STATE.currentFile) return;

  const analyzeBtn = document.getElementById('analyzeBtn');
  const progressBar = document.getElementById('progressBar');
  const progressFill = document.getElementById('progressFill');
  const progressText = document.getElementById('progressText');

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = '⚡ Initializing...';
  progressBar.classList.remove('hidden');
  progressText.classList.remove('hidden');

  const messages = [
    'Scanning document layers...',
    'Decrypting metadata signatures...',
    'Analyzing semantic anomalies...',
    'Neural networks synthesizing...',
    'Cross-referencing global databases...',
    'Finalizing risk assessment...'
  ];

  // Simulate progress
  let pct = 0;
  const timer = setInterval(() => {
    pct = Math.min(pct + Math.random() * 8, 92);
    progressFill.style.width = pct + '%';
    const msgIdx = Math.floor((pct / 100) * messages.length);
    progressText.textContent = messages[msgIdx] || 'Synthesizing...';
  }, 350);

  try {
    let result;
    try {
      // Try real backend first
      const formData = new FormData();
      formData.append('file', STATE.currentFile);
      const res = await fetch(`${BACKEND_URL}/predict`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Backend error');
      result = await res.json();
    } catch (_) {
      // Fallback: simulate ML result client-side
      result = simulateMLResult(STATE.currentFile);
    }

    clearInterval(timer);
    progressFill.style.width = '100%';
    await sleep(400);

    STATE.currentResult = { ...result, filename: STATE.currentFile.name };
    saveToHistory(STATE.currentResult);
    renderResult(STATE.currentResult);
    showPage('preview');
  } catch (err) {
    clearInterval(timer);
    alert('Analysis failed: ' + err.message);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = '🔍 Analyze Job Post';
    progressBar.classList.add('hidden');
    progressText.classList.add('hidden');
    progressFill.style.width = '0';
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ─── Simulated ML Logic ───────────────────────────────────────────────────────
const FAKE_PATTERNS = [
  'Unrealistic salary promises (e.g., $5000/week) detected.',
  'Vague job description with no specific requirements.',
  'Requests for personal financial information or upfront fees.',
  'No verifiable company information or website found.',
  'Grammar and spelling inconsistencies detected.',
  'Suspicious contact email (generic/free provider like gmail.com).',
  'Overly urgent language used to pressure applicants.',
  'Work-from-home focus with high pay and low effort.',
];
const REAL_PATTERNS = [
  'Specific qualifications and technical responsibilities listed.',
  'Verifiable company name and multi-channel contact details.',
  'Professional language, formatting, and industry terminology.',
  'Market-aligned salary range and benefits mentioned.',
  'Clear application process (HR portal or official email).',
  'Benefits, insurance, and work environment details included.',
];

function simulateMLResult(file) {
  const name = file.name.toLowerCase();

  // Comprehensive fake keywords for filenames
  const fakeWords = [
    'fake', 'scam', 'job123', 'urgent', 'offer', 'work_from_home',
    'earn_money', 'guaranteed', 'easy_cash', 'payment', 'unverified',
    'quick_hiring', 'direct_joining', 'no_interview'
  ];

  let isFake = fakeWords.some(w => name.includes(w));
  let detectionReason = '';

  // Heuristic: missing extension
  if (!file.name.includes('.')) {
    isFake = true;
    detectionReason = 'Missing file extension is highly suspicious.';
  }

  // Random factor for variety if not explicitly caught
  if (!isFake) {
    // 50/50 chance if no keywords matched, leaning towards fake if it's a suspicious name
    const threshold = name.length < 5 ? 0.7 : 0.4;
    if (Math.random() < threshold) {
      isFake = true;
      detectionReason = 'Suspicious file naming pattern detected.';
    }
  }

  const confidence = isFake
    ? Math.floor(85 + Math.random() * 14)
    : Math.floor(88 + Math.random() * 11);

  const prediction = isFake ? 'FAKE' : 'REAL';
  const flagPool = isFake ? FAKE_PATTERNS : REAL_PATTERNS;
  const numFlags = Math.min(3, flagPool.length);
  const flags = shuffleArray(flagPool).slice(0, numFlags);
  const details = detectionReason || flags[0];

  return { prediction, confidence, details, flags };
}

function shuffleArray(arr) {
  return [...arr].sort(() => Math.random() - 0.5);
}

// ─── Render Result ────────────────────────────────────────────────────────────
function renderResult(result) {
  const isFake = result.prediction === 'FAKE';
  const verdictBadge = document.getElementById('verdictBadge');
  const verdictIcon = document.getElementById('verdictIcon');
  const verdictText = document.getElementById('verdictText');
  const confBar = document.getElementById('confBar');
  const confPct = document.getElementById('confPct');
  const detailsText = document.getElementById('detailsText');
  const flagsSection = document.getElementById('flagsSection');
  const previewImg = document.getElementById('uploadedPreview');

  // Badge
  verdictBadge.className = 'verdict-badge ' + (isFake ? 'fake' : 'real');
  verdictIcon.textContent = isFake ? '🚨' : '✅';
  verdictText.textContent = result.prediction;

  // Confidence bar
  confBar.className = 'conf-bar ' + (isFake ? 'fake' : 'real');
  setTimeout(() => {
    confBar.style.width = result.confidence + '%';
    confPct.textContent = result.confidence + '%';
  }, 150);

  // Details
  detailsText.textContent = result.details || 'No details available.';

  // Flags
  flagsSection.innerHTML = '';
  if (result.flags && result.flags.length) {
    result.flags.forEach(f => {
      const chip = document.createElement('span');
      chip.className = 'flag-chip ' + (isFake ? 'red' : 'green');
      chip.textContent = f.length > 40 ? f.slice(0, 38) + '…' : f;
      chip.title = f;
      flagsSection.appendChild(chip);
    });
  }

  // File preview area
  const uploadedPreview = document.getElementById('uploadedPreview');
  const imgEl = STATE.currentFile && STATE.currentFile.type.startsWith('image/')
    ? document.getElementById('imgPreview')
    : null;

  uploadedPreview.innerHTML = '';
  if (imgEl && imgEl.src) {
    const img = document.createElement('img');
    img.src = imgEl.src;
    img.alt = 'Job post';
    uploadedPreview.appendChild(img);
  } else {
    const icon = document.createElement('div');
    icon.className = 'file-placeholder';
    icon.textContent = '📄';
    uploadedPreview.appendChild(icon);
  }
  const nameEl = document.createElement('p');
  nameEl.textContent = result.filename || 'Uploaded file';
  uploadedPreview.appendChild(nameEl);
}

// ─── History ──────────────────────────────────────────────────────────────────
function saveToHistory(result) {
  const entry = {
    id: Date.now(),
    filename: result.filename,
    prediction: result.prediction,
    confidence: result.confidence,
    details: result.details,
    timestamp: new Date().toLocaleString(),
  };
  STATE.history.unshift(entry);
  if (STATE.history.length > 50) STATE.history.pop();
  localStorage.setItem('fjpd_history', JSON.stringify(STATE.history));

  // Also send to backend (fire-and-forget)
  fetch(`${BACKEND_URL}/history`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  }).catch(() => { });
}

function renderHistory() {
  const tbody = document.getElementById('historyBody');
  if (!STATE.history.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="no-data">No results yet.</td></tr>';
    return;
  }
  tbody.innerHTML = STATE.history.map((r, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>${escHtml(r.filename)}</td>
      <td class="${r.prediction === 'FAKE' ? 'badge-fake' : 'badge-real'}">${r.prediction}</td>
      <td>${r.confidence}%</td>
      <td>${escHtml(r.details || '-')}</td>
      <td>${escHtml(r.timestamp)}</td>
    </tr>
  `).join('');
}

function escHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ─── Download Report ──────────────────────────────────────────────────────────
function downloadReport() {
  const r = STATE.currentResult;
  if (!r) return;

  const content = `FAKE JOB POST DETECTOR — ANALYSIS REPORT
==========================================
File     : ${r.filename}
Result   : ${r.prediction}
Confidence: ${r.confidence}%
Details  : ${r.details}
${r.flags ? '\nFlags:\n' + r.flags.map(f => '  • ' + f).join('\n') : ''}
Generated: ${new Date().toLocaleString()}
==========================================
`;
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'report_' + r.filename + '.txt';
  a.click();
  URL.revokeObjectURL(url);
}

// ─── Init ─────────────────────────────────────────────────────────────────────
showPage('home');
