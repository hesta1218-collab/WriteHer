const area = document.getElementById('writingArea');
const indicator = document.getElementById('saveIndicator');
let saveTimer = null;

area.addEventListener('input', () => {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(saveDraft, 1000);
});

function saveDraft() {
    fetch('/editor/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: PROJECT, content: area.value })
    }).then(() => {
        indicator.classList.add('show');
        setTimeout(() => indicator.classList.remove('show'), 2000);
    });
}

// 资料库展开/收起
let currentOpenSource = null;

function toggleSource(sourceId) {
    const contentDiv = document.getElementById('source-' + sourceId);

    // 如果点击的是当前打开的，就收起
    if (currentOpenSource === sourceId) {
        contentDiv.style.display = 'none';
        currentOpenSource = null;
        return;
    }

    // 收起之前打开的
    if (currentOpenSource) {
        document.getElementById('source-' + currentOpenSource).style.display = 'none';
    }

    // 如果内容还没加载，先加载
    if (!contentDiv.dataset.loaded) {
        fetch(`/api/source/${sourceId}`)
            .then(r => r.json())
            .then(data => {
                // 简单渲染 Markdown（只处理段落）
                const html = data.content.split('\n\n').map(p => {
                    if (p.startsWith('#')) return `<h3 style="margin:8px 0; font-size:14px;">${p.replace(/^#+\s*/, '')}</h3>`;
                    return `<p style="margin:8px 0;">${p}</p>`;
                }).join('');
                contentDiv.innerHTML = html;
                contentDiv.dataset.loaded = 'true';
                contentDiv.style.display = 'block';
            });
    } else {
        contentDiv.style.display = 'block';
    }

    currentOpenSource = sourceId;
}
