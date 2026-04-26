// 用 marked.js CDN 渲染 Markdown
const script = document.createElement('script');
script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
script.onload = () => {
    let html = marked.parse(RAW_CONTENT);
    // 恢复已保存的高亮
    EXISTING_CARDS.forEach((content, i) => {
        if (!content) return;
        const tags = JSON.parse(EXISTING_TAGS[i] || '[]');
        const tagStr = tags.join(' ');
        const escaped = content.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        html = html.replace(
            new RegExp(escaped, 'g'),
            `<span class="annotated" title="${tagStr}">$&</span><span class="inline-tag">${tagStr}</span>`
        );
    });
    document.getElementById('articleBody').innerHTML = html;
};
document.head.appendChild(script);

let selectedText = '';
let savedRange = null;
const popup = document.getElementById('tagPopup');
const tagInput = document.getElementById('tagInput');

document.getElementById('articlePanel').addEventListener('mouseup', (e) => {
    const sel = window.getSelection();
    const text = sel.toString().trim();
    if (!text) return;
    selectedText = text;
    // 保存选区范围
    savedRange = sel.rangeCount > 0 ? sel.getRangeAt(0).cloneRange() : null;
    popup.style.left = e.pageX + 'px';
    popup.style.top = (e.pageY - 60) + 'px';
    popup.classList.add('open');
    tagInput.value = '';
    tagInput.focus();
});

document.getElementById('tagConfirm').addEventListener('click', saveCard);
tagInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') saveCard(); });

function saveCard() {
    const raw = tagInput.value.trim();
    const tags = raw ? raw.split(/\s+/).map(t => t.startsWith('#') ? t : '#' + t) : [];

    fetch(`/reader/${SOURCE_ID}/card`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: selectedText, tags })
    }).then(() => {
        addCardToPanel(selectedText, tags);

        // 高亮标注的文本
        if (savedRange) {
            highlightRange(savedRange, tags);
        }

        popup.classList.remove('open');
        window.getSelection().removeAllRanges();
    });
}

function highlightRange(range, tags) {
    const span = document.createElement('span');
    span.className = 'annotated';
    span.title = tags.join(' ');
    try {
        range.surroundContents(span);
        // 在高亮文本后添加标签显示
        const tagSpan = document.createElement('span');
        tagSpan.className = 'inline-tag';
        tagSpan.textContent = tags.join(' ');
        span.parentNode.insertBefore(tagSpan, span.nextSibling);
    } catch (e) {
        // 如果选区跨越多个节点，用更复杂的方式处理
        console.warn('无法高亮跨节点选区', e);
    }
}

function addCardToPanel(content, tags) {
    const list = document.getElementById('cardsList');
    const div = document.createElement('div');
    div.className = 'card-item';
    div.innerHTML = `<div class="card-tags">${tags.join(' ')}</div>${content}`;
    list.prepend(div);
}

document.addEventListener('mousedown', (e) => {
    if (!popup.contains(e.target)) popup.classList.remove('open');
});
