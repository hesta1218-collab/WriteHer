const canvas = document.getElementById('canvas');
const edgesLayer = document.getElementById('edgesLayer');

let nodes = [];   // {id, card_id, x, y, label}
let edges = [];   // {id, from, to, label}
let edgeIdCounter = 0;
let selectedNodeId = null;
let connectingFrom = null;
let draggingNode = null;
let dragOffset = { x: 0, y: 0 };

// ── 初始化 ──────────────────────────────────────────────

function init() {
    nodes = INIT_NODES.map(n => ({ ...n }));
    edges = INIT_EDGES.map(e => ({ ...e }));
    edgeIdCounter = edges.reduce((m, e) => Math.max(m, e.id || 0), 0);
    nodes.forEach(renderNode);
    renderAllEdges();
}

// ── 节点渲染 ──────────────────────────────────────────────

function renderNode(n) {
    const el = document.createElement('div');
    el.className = 'board-node';
    el.id = 'node-' + n.id;
    el.style.left = n.x + 'px';
    el.style.top = n.y + 'px';
    el.innerHTML = `<span class="node-del" onclick="deleteNode('${n.id}')">✕</span>${n.label}`;
    el.addEventListener('mousedown', onNodeMouseDown);
    el.addEventListener('click', onNodeClick);
    canvas.appendChild(el);
}

function onNodeMouseDown(e) {
    if (e.target.classList.contains('node-del')) return;
    draggingNode = e.currentTarget;
    const rect = draggingNode.getBoundingClientRect();
    dragOffset.x = e.clientX - rect.left;
    dragOffset.y = e.clientY - rect.top;
    e.preventDefault();
}

document.addEventListener('mousemove', (e) => {
    if (!draggingNode) return;
    const canvasRect = canvas.getBoundingClientRect();
    const x = e.clientX - canvasRect.left - dragOffset.x;
    const y = e.clientY - canvasRect.top - dragOffset.y;
    draggingNode.style.left = x + 'px';
    draggingNode.style.top = y + 'px';
    const id = draggingNode.id.replace('node-', '');
    const n = nodes.find(n => String(n.id) === id);
    if (n) { n.x = x; n.y = y; }
    renderAllEdges();
});

document.addEventListener('mouseup', () => { draggingNode = null; });

function onNodeClick(e) {
    if (e.target.classList.contains('node-del')) return;
    const id = e.currentTarget.id.replace('node-', '');
    if (!connectingFrom) {
        // 第一次点击：选中，准备连线
        if (selectedNodeId === id) {
            clearSelection();
        } else {
            clearSelection();
            selectedNodeId = id;
            connectingFrom = id;
            e.currentTarget.classList.add('selected');
        }
    } else if (connectingFrom !== id) {
        // 第二次点击：连线
        addEdge(connectingFrom, id);
        clearSelection();
    }
}

function clearSelection() {
    selectedNodeId = null;
    connectingFrom = null;
    document.querySelectorAll('.board-node.selected').forEach(el => el.classList.remove('selected'));
}

document.getElementById('clearSelBtn').addEventListener('click', clearSelection);

// ── 边 ──────────────────────────────────────────────────

function addEdge(fromId, toId, label = '') {
    edgeIdCounter++;
    const edge = { id: edgeIdCounter, from: fromId, to: toId, label };
    edges.push(edge);
    renderAllEdges();
}

function renderAllEdges() {
    edgesLayer.innerHTML = '';
    edges.forEach(renderEdge);
}

function renderEdge(edge) {
    const fromEl = document.getElementById('node-' + edge.from);
    const toEl = document.getElementById('node-' + edge.to);
    if (!fromEl || !toEl) return;

    const canvasRect = canvas.getBoundingClientRect();
    const fr = fromEl.getBoundingClientRect();
    const tr = toEl.getBoundingClientRect();

    const x1 = fr.left + fr.width / 2 - canvasRect.left;
    const y1 = fr.top + fr.height / 2 - canvasRect.top;
    const x2 = tr.left + tr.width / 2 - canvasRect.left;
    const y2 = tr.top + tr.height / 2 - canvasRect.top;

    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1); line.setAttribute('y1', y1);
    line.setAttribute('x2', x2); line.setAttribute('y2', y2);
    line.style.pointerEvents = 'stroke';
    line.addEventListener('dblclick', (e) => openEdgeLabelPopup(e, edge));
    edgesLayer.appendChild(line);

    if (edge.label) {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', (x1 + x2) / 2);
        text.setAttribute('y', (y1 + y2) / 2 - 6);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('class', 'edge-label-text');
        text.textContent = edge.label;
        edgesLayer.appendChild(text);
    }
}

// ── 连线标注 ──────────────────────────────────────────────

let editingEdge = null;
const edgeLabelPopup = document.getElementById('edgeLabelPopup');
const edgeLabelInput = document.getElementById('edgeLabelInput');

function openEdgeLabelPopup(e, edge) {
    editingEdge = edge;
    edgeLabelInput.value = edge.label || '';
    edgeLabelPopup.style.left = e.pageX + 'px';
    edgeLabelPopup.style.top = (e.pageY - 50) + 'px';
    edgeLabelPopup.classList.add('open');
    edgeLabelInput.focus();
}

document.getElementById('edgeLabelConfirm').addEventListener('click', () => {
    if (editingEdge) {
        editingEdge.label = edgeLabelInput.value.trim();
        renderAllEdges();
    }
    edgeLabelPopup.classList.remove('open');
});

document.addEventListener('mousedown', (e) => {
    if (!edgeLabelPopup.contains(e.target)) edgeLabelPopup.classList.remove('open');
});

// ── 拖入卡片 ──────────────────────────────────────────────

document.querySelectorAll('.lib-card').forEach(card => {
    card.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('card_id', card.dataset.id);
        e.dataTransfer.setData('card_content', card.dataset.content);
    });
});

canvas.addEventListener('dragover', (e) => e.preventDefault());
canvas.addEventListener('drop', (e) => {
    e.preventDefault();
    const card_id = e.dataTransfer.getData('card_id');
    const label = e.dataTransfer.getData('card_content');
    const canvasRect = canvas.getBoundingClientRect();
    const x = e.clientX - canvasRect.left - 80;
    const y = e.clientY - canvasRect.top - 20;
    const id = Date.now().toString();
    const node = { id, card_id, x, y, label: label.slice(0, 100) };
    nodes.push(node);
    renderNode(node);
});

// ── 删除节点 ──────────────────────────────────────────────

function deleteNode(id) {
    nodes = nodes.filter(n => String(n.id) !== id);
    edges = edges.filter(e => String(e.from) !== id && String(e.to) !== id);
    const el = document.getElementById('node-' + id);
    if (el) el.remove();
    renderAllEdges();
}

// ── 保存 ──────────────────────────────────────────────────

document.getElementById('saveBtn').addEventListener('click', () => {
    fetch('/board/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: PROJECT, nodes, edges })
    }).then(() => {
        const btn = document.getElementById('saveBtn');
        btn.textContent = '已保存';
        setTimeout(() => { btn.textContent = '保存画布'; }, 1500);
    });
});

init();
