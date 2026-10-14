// 统一 API 请求封装
const API_BASE = '';

async function apiFetch(url, options = {}) {
    const defaultHeaders = { 'Content-Type': 'application/json' };
    const config = {
        ...options,
        headers: { ...defaultHeaders, ...options.headers },
    };
    try {
        const resp = await fetch(API_BASE + url, config);
        if (resp.status === 401) {
            showToast('请先登录', 'error');
            if (window.location.pathname !== '/') {
                window.location.href = '/';
            }
            throw new Error('Unauthorized');
        }
        if (resp.status === 429) {
            showToast('请求过于频繁，请稍后再试', 'error');
            throw new Error('RateLimited');
        }
        if (resp.status >= 500) {
            showToast('服务器错误，请稍后重试', 'error');
            throw new Error('ServerError');
        }
        const data = await resp.json();
        if (!resp.ok) {
            throw new Error(data.error || '请求失败');
        }
        return data;
    } catch (err) {
        if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
            showToast('网络连接失败，请检查网络', 'error');
        }
        throw err;
    }
}

function showToast(msg, type = 'info') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function showLoading(msg = '正在生成，请稍候...') {
    const existing = document.querySelector('.loading-overlay');
    if (existing) existing.remove();
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div style="text-align:center;color:#e6edf3;">
            <div class="spinner" style="margin:0 auto 16px;"></div>
            <p style="font-size:14px;">${msg}</p>
        </div>`;
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);display:flex;justify-content:center;align-items:center;z-index:1001;';
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) overlay.remove();
}

function validateGenerateForm(topic, keyword) {
    if (!topic || topic.trim().length < 1) {
        showToast('请输入文章主题', 'error');
        return false;
    }
    if (!keyword || keyword.trim().length < 1) {
        showToast('请输入关键词', 'error');
        return false;
    }
    if (topic.trim().length > 200) {
        showToast('主题不能超过200个字符', 'error');
        return false;
    }
    if (keyword.trim().length > 100) {
        showToast('关键词不能超过100个字符', 'error');
        return false;
    }
    return true;
}

        let selectedGenre = '散文';
        let selectedLength = 'medium';
        let lastArticleId = null;

        const lengthMap = { 0: ['short', '短篇'], 1: ['medium', '中篇'], 2: ['long', '长篇'], 3: ['long', '巨著'] };
        const articleWords = { 0: 2000, 1: 5000, 2: 10000, 3: 10000 };
        const novelWords = { 0: 150000, 1: 250000, 2: 300000, 3: 2000000 };
        let selectedCategory = 'article';
        const lengthWords = selectedCategory === 'novel' ? novelWords : articleWords;

        function selectQuickWords(words, el) {
            document.querySelectorAll('#quickWords .word-card').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            document.getElementById('customWords').value = words;
        }

        document.querySelectorAll('#genreGrid .genre-card').forEach(card => {
            card.addEventListener('click', () => {
                document.querySelectorAll('#genreGrid .genre-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                selectedGenre = card.dataset.value;
            });
        });

        function switchCategory(category, el) {
            selectedCategory = category;
            document.querySelectorAll('.config-group')[0].querySelectorAll('.method-card').forEach(c => c.classList.remove('active'));
            el.classList.add('active');
            const pg = document.getElementById('perspectiveGroup');
            if (pg) { pg.style.display = (category === 'novel') ? 'block' : 'none'; }
        }

        function toggleCollapse(bodyId, arrowId) {
            const body = document.getElementById(bodyId);
            const arrow = document.getElementById(arrowId);
            body.classList.toggle('show');
            arrow.textContent = body.classList.contains('show') ? '▲' : '▼';
        }

        function generate() {
            const topic = document.getElementById('topic').value.trim();
            const keyword = document.getElementById('keyword').value.trim();
            if (!topic || !keyword) { alert('请填写文章主题和关键词'); return; }

            const btn = document.getElementById('generateBtn');
            const empty = document.getElementById('workspaceEmpty');
            const container = document.getElementById('resultContainer');
            const body = document.getElementById('resultBody');

            btn.disabled = true;
            btn.textContent = '创作中...';
            empty.style.display = 'none';
            container.style.display = 'block';
            body.innerHTML = '<div class="loading-state"><div class="spinner"></div>正在创作中，请稍候...</div>';

            const isAI = true;
            const sliderVal = 0;
            const isShort = false;
            const isLong = true;
            const tags = document.getElementById('resultTags');
            const stats = document.getElementById('resultStats');

            const targetWords = Math.max(500, Math.min(2000000, parseInt(document.getElementById('customWords').value) || 2000));

            if (isLong) {
                let asyncBody = { genre: selectedGenre, topic, keyword, target_words: targetWords, is_ai: isAI, format_type: selectedCategory };
                if (isAI) {
                    asyncBody.style = document.getElementById('writingStyle').value;
                    if (selectedCategory === 'novel') {
                        asyncBody.perspective = document.getElementById('narrativePerspective').value;
                    }
                    asyncBody.language_style = document.getElementById('languageStyle').value;
                    asyncBody.constraints = document.getElementById('constraints').value;
                }

                body.innerHTML = '<div class="loading-state"><div class="spinner"></div>正在拟定大纲...</div>';

                fetch('/api/ai/outline', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(asyncBody)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.error) {
                        body.innerHTML = '<p style="color:var(--danger)">大纲生成失败：' + data.error + '</p>';
                        btn.disabled = false;
                        btn.textContent = '✨ 开始创作';
                        return;
                    }
                    showOutlineEditor(data.outline, asyncBody, btn, body, tags, stats, isAI);
                })
                .catch(() => {
                    body.innerHTML = '<p style="color:var(--danger)">请求失败，请重试</p>';
                    btn.disabled = false;
                    btn.textContent = '✨ 开始创作';
                });
                return;
            }

            let url = '/api/ai/generate';
            let body_data = { genre: selectedGenre, topic, keyword, length: selectedLength };
            body_data.style = document.getElementById('writingStyle').value;
            if (selectedCategory === 'novel') {
                body_data.perspective = document.getElementById('narrativePerspective').value;
            }
            body_data.language_style = document.getElementById('languageStyle').value;
            body_data.constraints = document.getElementById('constraints').value;
            body_data.format_type = selectedCategory;

            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body_data)
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    body.innerHTML = '<p style="color:var(--danger)">生成失败：' + data.error + '</p>';
                    return;
                }
                lastArticleId = data.article_id;

                const isLongResult = (data.chapters && data.chapters.length > 0);

                if (isLongResult) {
                    tags.innerHTML = '<span class="result-tag accent">' + data.genre + '</span><span class="result-tag">共 ' + data.chapter_count + ' 章</span><span class="result-tag">约 ' + data.actual_words + ' 字</span>' + (isAI ? '<span class="result-tag accent">🤖 AI</span>' : '');
                    stats.textContent = '阅读约 ' + Math.ceil(data.actual_words / 300) + ' 分钟';
                    let html = '';
                    data.chapters.forEach(ch => {
                        html += '<div class="chapter-block">';
                        html += '<div class="chapter-title">' + ch.chapter_title + '</div>';
                        html += '<div class="chapter-content">' + ch.content + '</div>';
                        html += '</div>';
                    });
                    body.innerHTML = html;
                } else {
                    const wc = data.content.replace(/\s/g, '').length;
                    tags.innerHTML = '<span class="result-tag accent">' + data.genre + '</span><span class="result-tag">约 ' + wc + ' 字</span>' + (isAI ? '<span class="result-tag accent">🤖 AI</span>' : '');
                    stats.textContent = '阅读约 ' + Math.ceil(wc / 300) + ' 分钟';
                    body.innerHTML = '<div class="result-content">' + data.content + '</div>';
                }
            })
            .catch(() => { body.innerHTML = '<p style="color:var(--danger)">请求失败，请重试</p>'; })
            .finally(() => { btn.disabled = false; btn.textContent = '✨ 开始创作'; });
        }

        function showOutlineEditor(outline, asyncBody, btn, body, tags, stats, isAI) {
            let html = '<div style="padding:8px 0 20px;">';
            html += '<div style="font-size:17px;font-weight:700;margin-bottom:8px;">📋 大纲已生成，请确认</div>';
            html += '<div style="font-size:13px;color:var(--text-muted);margin-bottom:20px;">您可以修改标题、删除或新增条目，确认后按此大纲逐节生成正文。</div>';
            html += '<div id="outlineList">';
            outline.forEach((item) => {
                const t = (item.chapter_title || '').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                html += '<div class="outline-row" style="display:flex;gap:8px;margin-bottom:10px;align-items:center;">';
                html += '<input type="text" class="input-field" style="flex:1;" value="' + t + '">';
                html += '<button class="action-btn danger" onclick="this.parentNode.remove()">删除</button>';
                html += '</div>';
            });
            html += '</div>';
            html += '<button class="action-btn" style="margin-top:6px;" onclick="addOutlineRow()">＋ 新增一节</button>';
            html += '<div style="margin-top:22px;display:flex;gap:10px;flex-wrap:wrap;">';
            html += '<button class="action-btn success" onclick="confirmOutline()">✅ 确认大纲，开始生成</button>';
            html += '<button class="action-btn" onclick="generate()">🔄 重新拟定</button>';
            html += '</div></div>';
            body.innerHTML = html;

            window._outlineBody = asyncBody;
            window._outlineBtn = btn;
            window._outlineTags = tags;
            window._outlineStats = stats;
            window._outlineIsAI = isAI;
        }

        function addOutlineRow() {
            const list = document.getElementById('outlineList');
            const row = document.createElement('div');
            row.className = 'outline-row';
            row.style.cssText = 'display:flex;gap:8px;margin-bottom:10px;align-items:center;';
            row.innerHTML = '<input type="text" class="input-field" style="flex:1;" placeholder="输入本节标题">' +
                '<button class="action-btn danger" onclick="this.parentNode.remove()">删除</button>';
            list.appendChild(row);
        }

        function confirmOutline() {
            const rows = document.querySelectorAll('#outlineList .outline-row input');
            const customOutline = [];
            rows.forEach((inp, i) => {
                const t = inp.value.trim();
                if (t) customOutline.push({ chapter_index: i + 1, chapter_title: t });
            });
            if (customOutline.length === 0) { alert('请至少保留一节'); return; }

            const body = document.getElementById('resultBody');
            const asyncBody = window._outlineBody;
            const btn = window._outlineBtn;
            const tags = window._outlineTags;
            const stats = window._outlineStats;
            const isAI = window._outlineIsAI;

            asyncBody.custom_outline = customOutline;
            asyncBody.is_ai = true;

            body.innerHTML = '<div class="loading-state"><div class="spinner"></div><div id="progressText">正在提交生成任务...</div><div style="margin-top:12px;width:100%;background:var(--bg-tertiary);border-radius:4px;overflow:hidden;"><div id="progressBar" style="width:0%;height:8px;background:var(--accent-grad);transition:width 0.5s;"></div></div><button class="action-btn danger" style="margin-top:16px;" id="cancelBtn" onclick="cancelGeneration()">取消生成</button></div>';

            fetch('/api/generate/async', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(asyncBody)
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    body.innerHTML = '<p style="color:var(--danger)">提交失败：' + data.error + '</p>';
                    btn.disabled = false;
                    btn.textContent = '✨ 开始创作';
                    return;
                }
                window.currentTaskId = data.task_id;
                pollGenerationStatus(data.task_id, btn, body, tags, stats, isAI);
            })
            .catch(() => {
                body.innerHTML = '<p style="color:var(--danger)">请求失败，请重试</p>';
                btn.disabled = false;
                btn.textContent = '✨ 开始创作';
            });
        }

        let pollTimer = null;

        function pollGenerationStatus(taskId, btn, body, tags, stats, isAI) {
            pollTimer = setInterval(() => {
                fetch('/api/generate/status/' + taskId)
                .then(res => res.json())
                .then(data => {
                    if (data.error) {
                        clearInterval(pollTimer);
                        body.innerHTML = '<p style="color:var(--danger)">查询失败：' + data.error + '</p>';
                        btn.disabled = false;
                        btn.textContent = '✨ 开始创作';
                        return;
                    }
                    const progressText = document.getElementById('progressText');
                    const progressBar = document.getElementById('progressBar');
                    if (data.status === 'generating') {
                        if (progressText) progressText.textContent = '正在生成第 ' + data.current_chapter + '/' + data.total_chapters + ' 章...';
                        if (progressBar) progressBar.style.width = data.progress + '%';
                    } else if (data.status === 'completed') {
                        clearInterval(pollTimer);
                        lastArticleId = data.article_id;
                        if (progressText) progressText.textContent = '生成完成！';
                        if (progressBar) progressBar.style.width = '100%';
                        tags.innerHTML = '<span class="result-tag accent">共 ' + data.chapter_count + ' 章</span><span class="result-tag">约 ' + data.actual_words + ' 字</span>' + (isAI ? '<span class="result-tag accent">🤖 AI</span>' : '');
                        stats.textContent = '阅读约 ' + Math.ceil(data.actual_words / 300) + ' 分钟';
                        body.innerHTML = '<div style="text-align:center;padding:40px;"><div style="font-size:48px;margin-bottom:16px;">✅</div><p style="font-size:18px;margin-bottom:8px;">生成完成！</p><p style="color:var(--text-muted);margin-bottom:20px;">共 ' + data.chapter_count + ' 章，约 ' + data.actual_words + ' 字</p><button class="action-btn" onclick="location.href=\'/article/' + data.article_id + '\'">📖 查看文章详情</button></div>';
                        btn.disabled = false;
                        btn.textContent = '✨ 开始创作';
                    } else if (data.status === 'failed') {
                        clearInterval(pollTimer);
                        body.innerHTML = '<p style="color:var(--danger)">生成失败：' + (data.error || '未知错误') + '</p>';
                        btn.disabled = false;
                        btn.textContent = '✨ 开始创作';
                    } else if (data.status === 'cancelled') {
                        clearInterval(pollTimer);
                        body.innerHTML = '<p style="color:var(--text-muted)">已取消生成</p>';
                        btn.disabled = false;
                        btn.textContent = '✨ 开始创作';
                    }
                })
                .catch(() => {});
            }, 3000);
        }

        function cancelGeneration() {
            if (window.currentTaskId) {
                fetch('/api/generate/cancel/' + window.currentTaskId, { method: 'POST' })
                .then(() => {})
                .catch(() => {});
            }
            if (pollTimer) clearInterval(pollTimer);
            const btn = document.getElementById('generateBtn');
            const body = document.getElementById('resultBody');
            if (btn) { btn.disabled = false; btn.textContent = '✨ 开始创作'; }
            if (body) { body.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px;">已取消生成</p>'; }
        }

        function copyResult() {
            const text = document.getElementById('resultBody').innerText;
            navigator.clipboard.writeText(text).then(() => alert('已复制到剪贴板'));
        }

        function downloadResult() {
            const text = document.getElementById('resultBody').innerText;
            const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'article_' + (lastArticleId || 'export') + '.txt';
            a.click();
        }

        function viewArticleDetail() {
            if (lastArticleId) { window.location.href = '/article/' + lastArticleId; }
        }

        let authMode = 'login';

        function openAuthModal(mode) {
            authMode = mode;
            document.getElementById('authModal').classList.add('show');
            document.getElementById('authTitle').textContent = mode === 'login' ? '登录' : '注册';
            document.getElementById('authSubmit').textContent = mode === 'login' ? '登录' : '注册';
            document.getElementById('switchText').textContent = mode === 'login' ? '还没有账号？' : '已有账号？';
            document.getElementById('switchLink').textContent = mode === 'login' ? '注册' : '登录';
            document.getElementById('authError').classList.remove('show');
        }

        function submitAuth() {
            const username = document.getElementById('authUsername').value.trim();
            const password = document.getElementById('authPassword').value.trim();
            const errorEl = document.getElementById('authError');

            if (!username || !password) {
                errorEl.textContent = '请填写用户名和密码';
                errorEl.classList.add('show');
                return;
            }

            fetch('/api/' + authMode, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    errorEl.textContent = data.error;
                    errorEl.classList.add('show');
                } else {
                    document.getElementById('authModal').classList.remove('show');
                    checkUserStatus();
                }
            })
            .catch(() => {
                errorEl.textContent = '请求失败，请重试';
                errorEl.classList.add('show');
            });
        }

        function checkUserStatus() {
            fetch('/api/user/status')
            .then(res => res.json())
            .then(data => {
                const userInfo = document.getElementById('userInfo');
                const authLink = document.getElementById('authLink');
                if (data.logged_in) {
                    userInfo.textContent = '👤 ' + data.username;
                    authLink.textContent = '退出';
                    authLink.onclick = () => {
                        fetch('/api/logout', { method: 'POST' })
                        .then(() => checkUserStatus());
                    };
                } else {
                    userInfo.textContent = '';
                    authLink.textContent = '登录';
                    authLink.onclick = () => openAuthModal('login');
                }
            });
        }

        checkUserStatus();
