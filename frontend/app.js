// ============ PARTICLE BACKGROUND ============
function initParticles() {
  const canvas = document.createElement('canvas');
  canvas.id = 'particleCanvas';
  canvas.style.cssText = 'position:fixed;inset:0;z-index:0;pointer-events:none;opacity:0.4;';
  document.body.prepend(canvas);
  const ctx = canvas.getContext('2d', { alpha: true });
  let particles = [];
  let animationId;
  
  function resize() { 
    canvas.width = window.innerWidth; 
    canvas.height = window.innerHeight;
    // Recreate particles on resize
    particles = [];
    const count = Math.min(120, Math.floor((canvas.width * canvas.height) / 15000));
    for (let i = 0; i < count; i++) particles.push(new Particle());
  }
  
  resize();
  window.addEventListener('resize', debounce(resize, 250));

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.size = Math.random() * 2 + 0.5;
      this.speedX = (Math.random() - 0.5) * 0.4;
      this.speedY = (Math.random() - 0.5) * 0.4;
      this.opacity = Math.random() * 0.6 + 0.1;
      this.color = Math.random() > 0.5 ? '#6ee7f7' : '#a78bfa';
    }
    update() {
      this.x += this.speedX; 
      this.y += this.speedY;
      if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
        this.reset();
      }
    }
    draw() {
      ctx.save();
      ctx.globalAlpha = this.opacity;
      ctx.fillStyle = this.color;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }

  function drawConnections() {
    const maxDist = 100;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        if (dist < maxDist) {
          ctx.save();
          ctx.globalAlpha = (1 - dist / maxDist) * 0.15;
          ctx.strokeStyle = '#6ee7f7';
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
          ctx.restore();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    animationId = requestAnimationFrame(animate);
  }
  
  animate();

  // Pause animation when tab is not visible
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(animationId);
    } else {
      animate();
    }
  });
}

// ============ UTILITY FUNCTIONS ============
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ============ SOUND EFFECTS ============
const AudioCtx = window.AudioContext || window.webkitAudioContext;
let audioCtx;

function playSound(type) {
  try {
    if (!audioCtx) audioCtx = new AudioCtx();
    
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain); 
    gain.connect(audioCtx.destination);
    osc.type = 'sine'; // Smoother sound

    const now = audioCtx.currentTime;

    if (type === 'upload') {
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.15);
      osc.frequency.exponentialRampToValueAtTime(1200, now + 0.3);
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
      osc.start(now); 
      osc.stop(now + 0.4);
    } else if (type === 'delete') {
      osc.frequency.setValueAtTime(300, now);
      osc.frequency.exponentialRampToValueAtTime(100, now + 0.2);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
      osc.start(now); 
      osc.stop(now + 0.2);
    } else if (type === 'click') {
      osc.frequency.setValueAtTime(600, now);
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
      osc.start(now); 
      osc.stop(now + 0.05);
    }
  } catch(e) {
    console.warn('Audio playback failed:', e);
  }
}

// ============ PAGE TRANSITIONS ============
function initPageTransitions() {
  const overlay = document.createElement('div');
  overlay.id = 'pageOverlay';
  overlay.style.cssText = `
    position:fixed;inset:0;z-index:99997;
    background:linear-gradient(135deg,#6ee7f7,#a78bfa);
    transform:translateX(-100%);
    transition:transform 0.4s cubic-bezier(0.77,0,0.175,1);
    pointer-events:none;
    will-change:transform;
  `;
  document.body.appendChild(overlay);

  document.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('http')) return;
    
    link.addEventListener('click', e => {
      e.preventDefault();
      playSound('click');
      overlay.style.transform = 'translateX(0)';
      setTimeout(() => { window.location.href = href; }, 400);
    });
  });

  // Animate in on load
  overlay.style.transform = 'translateX(0)';
  overlay.style.transition = 'none';
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      overlay.style.transition = 'transform 0.5s cubic-bezier(0.77,0,0.175,1)';
      overlay.style.transform = 'translateX(100%)';
    });
  });
}

// ============ API CONFIGURATION ============
// API defined in auth.js

// ============ THEME TOGGLE ============
const themeCheck = document.getElementById('themeCheck');
const savedTheme = localStorage.getItem('theme') || 'dark';

// Apply saved theme on load
document.documentElement.setAttribute('data-theme', savedTheme);
themeCheck.checked = savedTheme === 'dark';

themeCheck.addEventListener('change', () => {
  const theme = themeCheck.checked ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  playSound('click');
});

// ============ TOAST NOTIFICATIONS ============
function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.className = 'toast', 3000);
}

// ============ FILE UTILITIES ============
function getIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const icons = {
    pdf: '📄', 
    jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', webp: '🖼️', svg: '🖼️',
    mp4: '🎬', mov: '🎬', avi: '🎬', mkv: '🎬', webm: '🎬',
    mp3: '🎵', wav: '🎵', flac: '🎵', ogg: '🎵',
    zip: '🗜️', rar: '🗜️', '7z': '🗜️', tar: '🗜️', gz: '🗜️',
    doc: '📝', docx: '📝',
    xls: '📊', xlsx: '📊', 
    ppt: '📊', pptx: '📊',
    txt: '📃', md: '📃',
    js: '💻', py: '💻', html: '💻', css: '💻', json: '💻', 
    ts: '💻', jsx: '💻', tsx: '💻', php: '💻', java: '💻',
  };
  return icons[ext] || '📁';
}

function formatSize(bytes) {
  if (bytes === 0) return '0 B';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
  return (bytes / 1073741824).toFixed(1) + ' GB';
}

function isImageFile(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext);
}

// ============ LOAD FILES ============
async function loadFiles() {
  const btn = document.getElementById('refreshBtn');
  btn.classList.add('spinning');
  
  try {
    const res = await authFetch(`${API}/files/list`);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    
    const data = await res.json();
    renderFiles(data.files || []);
    updateStorage(data.files || []);
  } catch(e) {
    console.error('Load files error:', e);
    showToast('Could not connect to server', 'error');
  } finally {
    btn.classList.remove('spinning');
  }
}

// ============ UPDATE STORAGE ============
function updateStorage(files) {
  const st = document.getElementById('storageText');
  const fill = document.getElementById('storageFill');
  
  if (st) st.textContent = `${files.length} file${files.length !== 1 ? 's' : ''}`;
  if (fill) {
    const percentage = Math.min((files.length / 50) * 100, 100); // Changed to 50 max files
    fill.style.width = percentage + '%';
  }
}

// ============ RENDER FILES ============
function renderFiles(files) {
  const grid = document.getElementById('filesGrid');
  
  if (!files.length) {
    grid.innerHTML = '<div class="empty-state"><p>📂 No files yet. Upload something awesome!</p></div>';
    return;
  }
  
  grid.innerHTML = '';
  
  files.forEach((file, i) => {
    const card = document.createElement('div');
    card.className = 'file-card';
    card.style.animationDelay = `${i * 0.05}s`;
    
    const date = new Date(file.last_modified).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
    
    const isImage = isImageFile(file.filename);
    const previewHTML = isImage 
      ? `<div class="img-preview-wrap">
           <img class="img-preview" src="${API}/files/download/${encodeURIComponent(file.filename)}" 
                alt="${file.filename}" 
                onerror="this.style.display='none'; this.parentElement.innerHTML='<div class=\\'file-icon-wrap\\'>${getIcon(file.filename)}</div>';"
                onload="this.style.display='block';">
         </div>`
      : `<div class="img-preview-wrap"><div class="file-icon-wrap">${getIcon(file.filename)}</div></div>`;
    
    card.innerHTML = `
      ${previewHTML}
      <div class="file-name" title="${file.filename}">${file.filename}</div>
      <div class="file-meta">${formatSize(file.size)} · ${date}</div>
      <div class="file-actions">
        <button class="btn-download" onclick="downloadFile('${escapeHtml(file.filename)}')">↓</button>
        <button class="btn-copy" onclick="copyFileLink('${escapeHtml(file.filename)}')">📋</button>
        <button class="btn-delete" onclick="deleteFile('${escapeHtml(file.filename)}', this)">✕</button>
      </div>
    `;
    
    grid.appendChild(card);
  });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

// ============ UPLOAD FILE ============
async function uploadFile(file) {
  // Validate file size (50MB max)
  const maxSize = 50 * 1024 * 1024;
  if (file.size > maxSize) {
    showToast('File too large! Max 50MB', 'error');
    return;
  }

  const progress = document.getElementById('uploadProgress');
  const bar = document.getElementById('progressBar');
  const text = document.getElementById('progressText');
  
  progress.classList.remove('hidden');
  bar.style.width = '0%';
  text.textContent = `Uploading ${file.name}...`;
  
  playSound('upload');
  
  let p = 0;
  const interval = setInterval(() => {
    p = Math.min(p + Math.random() * 15, 85);
    bar.style.width = p + '%';
  }, 200);
  
  try {
    const form = new FormData();
    form.append('file', file);
    
    const res = await authFetch(`${API}/files/upload`, { 
      method: 'POST', 
      body: form 
    });
    
    const data = await res.json();
    
    clearInterval(interval);
    bar.style.width = '100%';
    text.textContent = '✓ Uploaded!';
    
    setTimeout(() => { 
      progress.classList.add('hidden'); 
      bar.style.width = '0%'; 
    }, 1500);
    
    if (data.success) { 
      showToast(`✓ ${file.name} uploaded!`, 'success'); 
      loadFiles(); 
    } else {
      showToast(data.error || 'Upload failed', 'error');
    }
  } catch(e) {
    clearInterval(interval);
    progress.classList.add('hidden');
    console.error('Upload error:', e);
    showToast('Upload error: ' + e.message, 'error');
  }
}

// ============ DOWNLOAD FILE ============
async function downloadFile(filename) {
  try {
    const res = await authFetch(`${API}/files/download/${encodeURIComponent(filename)}`);
    const data = await res.json();
    
    if (data.url) { 
      window.open(data.url, '_blank'); 
      showToast(`↓ Downloading ${filename}`, 'success'); 
    } else {
      showToast('Download failed', 'error');
    }
  } catch(e) { 
    console.error('Download error:', e);
    showToast('Download failed', 'error'); 
  }
}

// ============ COPY FILE LINK ============
async function copyFileLink(filename) {
  try {
    const url = `${API}/files/download/${encodeURIComponent(filename)}`;
    await navigator.clipboard.writeText(url);
    showToast('📋 Link copied!', 'success');
    playSound('click');
  } catch(e) {
    console.error('Copy error:', e);
    showToast('Could not copy link', 'error');
  }
}

// ============ DELETE FILE ============
async function deleteFile(filename, btn) {
  if (!confirm(`Delete "${filename}"?`)) return;
  
  const card = btn.closest('.file-card');
  card.style.transform = 'scale(0.9)';
  card.style.opacity = '0.5';
  
  playSound('delete');
  
  try {
    const res = await authFetch(`${API}/files/${encodeURIComponent(filename)}`, { 
      method: 'DELETE' 
    });
    const data = await res.json();
    
    if (data.success) {
      card.style.transition = 'all 0.3s';
      card.style.transform = 'scale(0)';
      card.style.opacity = '0';
      setTimeout(() => loadFiles(), 300);
      showToast(`✓ ${filename} deleted`, 'success');
    } else {
      card.style.transform = '';
      card.style.opacity = '';
      showToast(data.error || 'Delete failed', 'error');
    }
  } catch(e) {
    card.style.transform = '';
    card.style.opacity = '';
    console.error('Delete error:', e);
    showToast('Delete failed', 'error');
  }
}

// ============ AI SEARCH ============
document.getElementById('searchBtn')?.addEventListener('click', async () => {
  const input = document.getElementById('searchInput');
  const query = input.value.trim();
  
  if (!query) {
    showToast('Please enter a search query', 'error');
    return;
  }
  
  const btn = document.getElementById('searchBtn');
  const result = document.getElementById('aiResult');
  const originalText = btn.textContent;
  
  btn.textContent = '⏳ Searching...'; 
  btn.disabled = true;
  
  try {
    const res = await authFetch(`${API}/search/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    
    const data = await res.json();
    result.classList.remove('hidden');
    
    if (data.success) {
      const matchText = data.total_matches === 1 ? 'match' : 'matches';
      result.innerHTML = `
        <h4>✦ AI Result — ${data.total_matches} ${matchText}</h4>
        <p>${data.explanation || 'Search complete.'}</p>
        ${data.results.length ? `
          <p style="margin-top:8px;color:var(--text)">
            Files: ${data.results.map(f => `<strong>${escapeHtml(f.filename)}</strong>`).join(', ')}
          </p>
        ` : ''}
      `;
    } else {
      result.innerHTML = `<h4>❌ Error</h4><p>${escapeHtml(data.error || 'Unknown error')}</p>`;
    }
  } catch(e) {
    console.error('Search error:', e);
    result.classList.remove('hidden');
    result.innerHTML = `<h4>❌ Error</h4><p>Could not reach AI service.</p>`;
  } finally {
    btn.textContent = originalText; 
    btn.disabled = false;
  }
});

document.getElementById('searchInput')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('searchBtn')?.click();
});

// ============ DRAG AND DROP ============
const uploadZone = document.getElementById('uploadZone');

uploadZone?.addEventListener('dragover', e => { 
  e.preventDefault(); 
  uploadZone.classList.add('dragover'); 
});

uploadZone?.addEventListener('dragleave', () => {
  uploadZone.classList.remove('dragover');
});

uploadZone?.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('dragover');
  
  const files = Array.from(e.dataTransfer.files);
  if (files.length === 0) return;
  
  files.forEach(uploadFile);
});

// ============ FILE INPUT ============
document.getElementById('fileInput')?.addEventListener('change', e => {
  const files = Array.from(e.target.files);
  files.forEach(uploadFile);
  e.target.value = ''; // Reset input
});

uploadZone?.addEventListener('click', e => {
  if (e.target.tagName !== 'LABEL') {
    document.getElementById('fileInput')?.click();
  }
});

// ============ REFRESH BUTTON ============
document.getElementById('refreshBtn')?.addEventListener('click', loadFiles);

// ============ CUSTOM CURSOR ============
const dot = document.getElementById('cursorDot');
const ring = document.getElementById('cursorRing');

if (dot && ring) {
  let mouseX = 0, mouseY = 0;
  let ringX = 0, ringY = 0;

  document.addEventListener('mousemove', e => {
    mouseX = e.clientX; 
    mouseY = e.clientY;
    dot.style.left = mouseX + 'px';
    dot.style.top = mouseY + 'px';
  });

  // Ring follows with smooth lag
  function animateRing() {
    ringX += (mouseX - ringX) * 0.12;
    ringY += (mouseY - ringY) * 0.12;
    ring.style.left = ringX + 'px';
    ring.style.top = ringY + 'px';
    requestAnimationFrame(animateRing);
  }
  animateRing();

  // Hover effect on interactive elements
  const interactiveSelectors = 'a, button, label, input, textarea, select, .file-card, .nav-link, .upload-zone';
  
  document.querySelectorAll(interactiveSelectors).forEach(el => {
    el.addEventListener('mouseenter', () => {
      dot.classList.add('hovering');
      ring.classList.add('hovering');
    });
    el.addEventListener('mouseleave', () => {
      dot.classList.remove('hovering');
      ring.classList.remove('hovering');
    });
  });

  // Click effect
  document.addEventListener('mousedown', () => {
    dot.classList.add('clicking');
    ring.classList.add('clicking');
  });
  
  document.addEventListener('mouseup', () => {
    dot.classList.remove('clicking');
    ring.classList.remove('clicking');
  });
  
  // Hide cursor on mobile/tablet
  if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
    dot.style.display = 'none';
    ring.style.display = 'none';
  }
}

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initPageTransitions();
  loadFiles();
});

// ============ KEYBOARD SHORTCUTS ============
document.addEventListener('keydown', e => {
  // Ctrl/Cmd + U = Upload
  if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
    e.preventDefault();
    document.getElementById('fileInput')?.click();
  }
  
  // Ctrl/Cmd + R = Refresh
  if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
    e.preventDefault();
    loadFiles();
  }
  
  // Escape = Close AI result
  if (e.key === 'Escape') {
    document.getElementById('aiResult')?.classList.add('hidden');
  }
});