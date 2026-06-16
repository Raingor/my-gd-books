// ─── Dark Mode Toggle ───
function toggleDark() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeButton();
}

function updateThemeButton() {
    const btn = document.getElementById('dark-btn');
    if (!btn) return;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    btn.textContent = isDark ? '☀️ 日间模式' : '🌙 夜间模式';
}

// Initialize theme
(function() {
    const saved = localStorage.getItem('theme');
    const prefers = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefers ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateThemeButton);
    } else {
        updateThemeButton();
    }
})();

// ─── Font Size Control ───
function changeFont(delta) {
    const current = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const next = Math.max(14, Math.min(22, current + delta));
    document.documentElement.style.fontSize = next + 'px';
    localStorage.setItem('fontSize', next);
}

// Restore font size
(function() {
    const saved = localStorage.getItem('fontSize');
    if (saved) {
        document.documentElement.style.fontSize = saved + 'px';
    }
})();

// ─── Scroll Progress ───
(function() {
    const bar = document.getElementById('scroll-bar');
    if (!bar) return;
    
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                const scrolled = window.scrollY;
                const total = document.documentElement.scrollHeight - window.innerHeight;
                const pct = total > 0 ? (scrolled / total) * 100 : 0;
                bar.style.width = pct + '%';
                ticking = false;
            });
            ticking = true;
        }
    });
})();

// ─── Menu Toggle ───
(function() {
    const menuBtn = document.querySelector('.menu-btn');
    const overlay = document.getElementById('nav-overlay');
    if (!menuBtn || !overlay) return;
    
    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        overlay.classList.toggle('open');
    });
    
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.classList.remove('open');
        }
    });
    
    // Close on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('open')) {
            overlay.classList.remove('open');
        }
    });
})();

// ─── Remember Reading Position ───
(function() {
    const key = 'lastRead_' + location.pathname;
    const saved = localStorage.getItem(key);
    
    if (saved && !location.hash) {
        const pos = parseInt(saved);
        if (pos > 0) {
            setTimeout(() => window.scrollTo(0, pos), 100);
        }
    }
    
    let saveTimeout;
    window.addEventListener('scroll', () => {
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(() => {
            localStorage.setItem(key, window.scrollY);
        }, 500);
    });
})();

// ─── Smooth Chapter Links ───
(function() {
    document.querySelectorAll('.ch-list a, .overlay-list a').forEach(link => {
        link.addEventListener('click', () => {
            const overlay = document.getElementById('nav-overlay');
            if (overlay) overlay.classList.remove('open');
        });
    });
})();
