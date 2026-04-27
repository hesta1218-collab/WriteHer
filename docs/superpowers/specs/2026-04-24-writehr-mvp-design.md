# WriteHer · 述她 MVP 设计文档

**日期**：2026-04-24  
**范围**：单用户本地 Web 应用，三个模块：资料库、侦探板、编辑器  
**运行方式**：Flask 本地服务，浏览器打开，无需部署

---

## 一、整体架构

```
writehr/
├── app.py              # Flask 入口，路由注册
├── db.py               # SQLite，现有文件扩展
├── static/
│   ├── style.css       # 全局样式（深色主题，暖金色）
│   └── js/
│       ├── library.js  # 资料库交互
│       ├── reader.js   # 资料阅读器（标注/标签）
│       ├── board.js    # 侦探板画布
│       └── editor.js   # 编辑器面板控制
└── templates/
    ├── base.html       # 公共导航、字体、CSS变量
    ├── library.html    # 资料库页面
    ├── reader.html     # 资料阅读/标注页面
    ├── board.html      # 侦探板页面
    └── editor.html     # 四栏编辑器页面
```

**技术栈**：Flask + SQLite + 原生 JS，不引入前端框架。

**数据流**：
- 用户导入 Markdown → 存入 SQLite → 资料库展示
- 用户选中文本 + 加标签 → 该段落存为细节卡片
- 卡片拖入侦探板 → 用户连线 → 调用 Claude 生成大纲
- 编辑器加载资料 + 卡片 + 侦探板，支持自由写作

---

## 二、数据库 Schema（扩展现有 db.py）

```sql
-- 资料库
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    folder TEXT,                    -- 文件夹/分类名
    content TEXT NOT NULL,          -- Markdown 原文
    credibility TEXT,               -- '●' / '◐' / '○' / '◻'
    credibility_label TEXT,         -- '一手/案卷档案' 等描述
    created_at TEXT
);

-- 细节卡片（用户标注生成）
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER REFERENCES sources(id),
    content TEXT NOT NULL,          -- 被标注的原文段落
    tags TEXT,                      -- JSON: ["性格/执着", "环境/严酷"]
    created_at TEXT
);

-- 侦探板状态（每个项目一个画布）
CREATE TABLE IF NOT EXISTS board_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    nodes TEXT NOT NULL,            -- JSON: [{id, card_id, x, y, label}]
    edges TEXT NOT NULL,            -- JSON: [{from, to, label}]
    updated_at TEXT
);

-- 写作草稿
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    content TEXT,
    updated_at TEXT
);
```

---

## 三、模块设计

### 3.1 资料库（`/library`）

**视觉**：参照 HTML mockup 一（深色背景，左侧文件夹树，右侧资料列表，四列：可信度符号、标题、标签、日期）

**功能**：
- 左侧文件夹树：按 `folder` 字段分组，点击过滤
- 导入：点击"掷入新的碎片资料"，选择本地 `.md` 文件，解析标题（取文件名）和内容，存入 `sources` 表
- 可信度标签：每行右侧下拉选择 `●/◐/○/◻`，同时可填写子标签描述（如"一手/案卷档案"），即时保存
- 搜索：按标题全文检索
- 点击资料标题 → 进入阅读/标注页面（`/reader/<id>`）

### 3.2 资料阅读器（`/reader/<id>`）

**视觉**：参照 HTML mockup 二（双栏：左侧正文，右侧实时标签流）

**功能**：
- 渲染 Markdown 原文（用 marked.js 前端渲染，不引入后端依赖）
- 用户选中文本 → 弹出小浮层，输入 `#标签/子标签`，支持多个标签
- 确认后：
  - 该段文字底部出现金色下划线高亮
  - 标签显示在段落右侧（行内，金色小字）
  - 该段落 + 标签作为一张细节卡片存入 `cards` 表
- 右侧面板：实时显示本资料所有已标注的卡片列表（flomo 风格流）

### 3.3 侦探板（`/board`）

**视觉**：参照 HTML mockup 三右下角（深色网格背景，金色描边卡片节点，金色连线）

**功能**：
- 左侧卡片库：列出所有 `cards` 表中的卡片，可拖拽到画布
- 画布：自由拖拽定位卡片节点
- 连线：点击一个节点 → 点击另一个节点 → 自动连线（SVG 绘制）
- 连线标注：双击连线可添加关系描述（如"因果"、"转折"）
- 画布状态自动保存到 `board_state` 表（按项目名区分）
- **生成大纲**：点击按钮 → 将所有节点内容 + 连线关系发送给 Claude API → 返回结构化大纲 → 显示在侧边弹窗，可一键复制到编辑器

### 3.4 编辑器（`/editor`）

**视觉**：参照 HTML mockup 三（四栏网格布局，顶部导航条）

**布局**（CSS Grid，比例可调）：
- 左上：资料库面板（滚动列表，点击跳转到阅读器）
- 左下：细节卡片面板（卡片流）
- 右上：写作区（`<textarea>`，全屏沉浸感）
- 右下：侦探板缩略图（嵌入 iframe 或缩小版画布）

**面板控制**：
- 每个面板右上角有三个图标：最小化（收起到标题栏）、最大化（占满左半或右半）、关闭（隐藏）
- 面板宽度可拖拽调整（CSS resize 或手写 drag handler）

**写作区**：
- 自动保存到 `drafts` 表（debounce 1秒）
- 项目名来自 URL 参数（如 `/editor?project=苏珊·所罗门`）

---

## 四、页面导航

```
/                → 重定向到 /library
/library         → 资料库
/reader/<id>     → 资料阅读/标注
/board           → 侦探板（可加 ?project=xxx）
/editor          → 四栏编辑器（可加 ?project=xxx）
```

顶部简单导航条：资料库 / 侦探板 / 编辑器（三个链接）

---

## 五、视觉规范（沿用 HTML mockup 中的 CSS 变量）

```css
--bg-deep: #0a0a0a;
--panel-bg: #141414;
--text-warm: #ece5d8;
--border-muted: #2a2a2a;
--accent-gold: #8b7355;
--accent-gold-dim: #4d4438;
font-family: 'Noto Serif SC', serif;
```

---

## 六、超出 MVP 范围（暂不做）

- 多用户/登录
- 云端同步
- 图片资源搜索
- 写作内容与原始资料的双向溯源高亮
- WriteHer CLI 的自动抓取功能集成到 Web 界面
