let activeCredId = null;
const dropdown = document.getElementById('credDropdown');

function toggleCredDropdown(e, id) {
    e.stopPropagation();
    activeCredId = id;
    dropdown.style.display = 'block';
    dropdown.style.left = e.pageX + 'px';
    dropdown.style.top = e.pageY + 'px';
}

function setCred(symbol, label) {
    if (!activeCredId) return;
    fetch(`/library/credibility/${activeCredId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credibility: symbol, label })
    }).then(() => location.reload());
    dropdown.style.display = 'none';
}

document.addEventListener('click', () => { dropdown.style.display = 'none'; });

// 分享设置
let activeShareId = null;

function openShareSettings(id, isPublic, allowDownload) {
    activeShareId = id;
    document.getElementById('sharePublic').checked = isPublic === 1;
    document.getElementById('shareDownload').checked = allowDownload === 1;
    document.getElementById('shareModal').classList.add('open');
}

function saveShareSettings() {
    if (!activeShareId) return;
    const isPublic = document.getElementById('sharePublic').checked ? 1 : 0;
    const allowDownload = document.getElementById('shareDownload').checked ? 1 : 0;

    fetch(`/library/share/${activeShareId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_public: isPublic, allow_download: allowDownload })
    }).then(() => {
        location.reload();
    });
}

