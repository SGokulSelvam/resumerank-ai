/* ─── ResumeRank AI · main.js ────────────────────────── */

const form          = document.getElementById('ats-form');
const dropZone      = document.getElementById('drop-zone');
const dropContent   = document.getElementById('drop-content');
const dropPreview   = document.getElementById('drop-preview');
const resumeInput   = document.getElementById('resume-input');
const fileNameEl    = document.getElementById('file-name');
const fileSizeEl    = document.getElementById('file-size');
const fileIconEl    = document.getElementById('file-icon');
const fileRemoveBtn = document.getElementById('file-remove');
const jdTextarea    = document.getElementById('job-description');
const charCountEl   = document.getElementById('char-count');
const checkBtn      = document.getElementById('check-btn');
const btnText       = checkBtn?.querySelector('.btn-text');
const btnLoading    = checkBtn?.querySelector('.btn-loading');
const resultsSection = document.getElementById('results-section');
const checkerSection = document.querySelector('.checker-section');

let selectedFile = null;

/* ─── FILE ICONS ──────────────────────────────────────── */
const fileIcons = { pdf: '📕', doc: '📘', docx: '📘', txt: '📝' };

function getExt(name) { return name.split('.').pop().toLowerCase(); }

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

/* ─── DRAG & DROP ─────────────────────────────────────── */
if (dropZone) {
  dropZone.addEventListener('click', (e) => {
    if (e.target !== fileRemoveBtn) resumeInput.click();
  });

  ['dragenter', 'dragover'].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault(); dropZone.classList.add('drag-over');
    });
  });
  ['dragleave', 'drop'].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault(); dropZone.classList.remove('drag-over');
    });
  });
  dropZone.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  resumeInput.addEventListener('change', () => {
    if (resumeInput.files[0]) handleFile(resumeInput.files[0]);
  });

  fileRemoveBtn.addEventListener('click', (e) => {
    e.stopPropagation(); clearFile();
  });
}

function handleFile(file) {
  const ext = getExt(file.name);
  const allowed = ['pdf', 'doc', 'docx', 'txt'];
  if (!allowed.includes(ext)) {
    showToast('File type not supported. Please use PDF, DOC, DOCX, or TXT.');
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('File too large. Maximum 5MB for free users.');
    return;
  }
  selectedFile = file;
  fileNameEl.textContent = file.name;
  fileSizeEl.textContent = formatSize(file.size);
  fileIconEl.textContent = fileIcons[ext] || '📄';
  dropContent.style.display = 'none';
  dropPreview.style.display = 'flex';
  updateSubmitBtn();
}

function clearFile() {
  selectedFile = null;
  resumeInput.value = '';
  dropContent.style.display = '';
  dropPreview.style.display = 'none';
  updateSubmitBtn();
}

/* ─── TEXTAREA CHAR COUNT ─────────────────────────────── */
if (jdTextarea) {
  jdTextarea.addEventListener('input', () => {
    const len = jdTextarea.value.length;
    charCountEl.textContent = len.toLocaleString() + ' characters';
    charCountEl.style.color = len > 50 ? 'var(--green)' : 'var(--muted)';
    updateSubmitBtn();
  });
}

function updateSubmitBtn() {
  if (!checkBtn) return;
  const ready = selectedFile && jdTextarea?.value.trim().length > 30;
  checkBtn.disabled = !ready;
}

/* ─── FORM SUBMIT ─────────────────────────────────────── */
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!selectedFile) { showToast('Please upload a resume file.'); return; }
    if (jdTextarea.value.trim().length < 30) { showToast('Please paste a longer job description.'); return; }

    setLoading(true);

    const formData = new FormData();
    formData.append('resume', selectedFile);
    formData.append('job_description', jdTextarea.value);

    try {
      const res = await fetch('/analyze', { method: 'POST', body: formData });
      const data = await res.json();

      if (!res.ok) {
        showToast(data.detail || 'Analysis failed. Please try again.');
        setLoading(false);
        return;
      }

      renderResults(data);
      resultsSection.style.display = 'block';
      checkerSection.style.display = 'none';

      setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (err) {
      showToast('Network error. Please check your connection.');
    } finally {
      setLoading(false);
    }
  });
}

function setLoading(state) {
  checkBtn.disabled = state;
  btnText.style.display = state ? 'none' : 'flex';
  btnLoading.style.display = state ? 'flex' : 'none';
}

/* ─── RENDER RESULTS ──────────────────────────────────── */
function renderResults(data) {
  const score = data.ats_score || 0;
  const circumference = 314;

  // Score ring animation
  const ringFill = document.getElementById('ring-fill');
  const offset = circumference - (score / 100) * circumference;
  const scoreEl = document.getElementById('score-number');

  ringFill.style.strokeDashoffset = circumference;
  // Color ring based on score
  const ringColor = score >= 75 ? 'var(--green)' : score >= 50 ? 'var(--gold)' : 'var(--red)';
  ringFill.style.stroke = ringColor;
  ringFill.style.filter = `drop-shadow(0 0 6px ${ringColor})`;

  setTimeout(() => { ringFill.style.strokeDashoffset = offset; }, 100);

  // Animate score number
  animateNumber(scoreEl, 0, score, 1400);

  // Grade
  const gradeEl = document.getElementById('score-grade');
  gradeEl.textContent = data.grade || '–';
  gradeEl.style.color = score >= 75 ? 'var(--green)' : score >= 50 ? 'var(--gold)' : 'var(--red)';

  // Summary
  document.getElementById('score-summary').textContent = data.summary || '';

  // Keyword match
  const kwMatch = data.keyword_match || {};
  const matchPct = kwMatch.match_percentage || 0;
  document.getElementById('match-fill').style.width = matchPct + '%';
  document.getElementById('match-pct').textContent = matchPct + '%';

  const matchedEl = document.getElementById('matched-keywords');
  const missingEl = document.getElementById('missing-keywords');
  matchedEl.innerHTML = (kwMatch.matched_keywords || []).slice(0,10)
    .map(k => `<span class="chip chip-match">${escHtml(k)}</span>`).join('');
  missingEl.innerHTML = (kwMatch.missing_keywords || []).slice(0,10)
    .map(k => `<span class="chip chip-miss">${escHtml(k)}</span>`).join('');

  // Section Analysis
  const sectionsEl = document.getElementById('sections-grid');
  const sectionData = data.sections_analysis || {};
  const sectionLabels = {
    contact_info: 'Contact Info',
    work_experience: 'Work Experience',
    education: 'Education',
    skills: 'Skills',
    formatting: 'Formatting'
  };

  sectionsEl.innerHTML = Object.entries(sectionData).map(([key, val]) => {
    const barClass = val.status === 'good' ? 'bar-good' : val.status === 'warning' ? 'bar-warn' : 'bar-miss';
    const scoreColor = val.status === 'good' ? 'var(--green)' : val.status === 'warning' ? 'var(--gold)' : 'var(--red)';
    return `
      <div class="section-item">
        <div class="section-name">${sectionLabels[key] || key}</div>
        <div class="section-bar">
          <div class="section-bar-fill ${barClass}" style="width:${val.score || 0}%"></div>
        </div>
        <div class="section-score" style="color:${scoreColor}">${val.score || 0}</div>
        <div class="section-note">${escHtml(val.note || '')}</div>
      </div>`;
  }).join('');

  // Strengths
  const strengthsEl = document.getElementById('strengths-list');
  strengthsEl.innerHTML = (data.strengths || [])
    .map(s => `<li>${escHtml(s)}</li>`).join('');

  // Quick Wins
  const qwEl = document.getElementById('quickwins-list');
  qwEl.innerHTML = (data.quick_wins || [])
    .map(q => `<li>${escHtml(q)}</li>`).join('');

  // Suggestions
  const suggestionsEl = document.getElementById('suggestions-list');
  suggestionsEl.innerHTML = (data.suggestions || []).map(s => `
    <div class="suggestion-item">
      <span class="priority-badge priority-${s.priority || 'low'}">${(s.priority || 'low').toUpperCase()}</span>
      <div class="suggestion-body">
        <div class="suggestion-cat">${escHtml(s.category || '')}</div>
        <div class="suggestion-title">${escHtml(s.title || '')}</div>
        <div class="suggestion-desc">${escHtml(s.description || '')}</div>
        ${s.example ? `<div class="suggestion-example">💡 ${escHtml(s.example)}</div>` : ''}
      </div>
    </div>`).join('');
}

/* ─── RECHECK BUTTON ──────────────────────────────────── */
const recheckBtn = document.getElementById('btn-recheck');
if (recheckBtn) {
  recheckBtn.addEventListener('click', () => {
    resultsSection.style.display = 'none';
    checkerSection.style.display = 'block';
    clearFile();
    jdTextarea.value = '';
    charCountEl.textContent = '0 characters';
    updateSubmitBtn();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ─── UTILITIES ───────────────────────────────────────── */
function animateNumber(el, start, end, duration) {
  const range = end - start;
  const startTime = performance.now();
  function step(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + range * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function escHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function showToast(msg, duration = 4000) {
  const toast = document.getElementById('error-toast');
  const msgEl = document.getElementById('toast-msg');
  if (!toast || !msgEl) return;
  msgEl.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), duration);
}

/* ─── SCROLL REVEAL ───────────────────────────────────── */
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.how-card, .feature-card, .pricing-card, .faq-item').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  observer.observe(el);
});
