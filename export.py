import os
from datetime import datetime, timezone
from pathlib import Path


OBSIDIAN_FOLDER = Path("/Users/jean/内容创作/资料/人物")

CREDIBILITY = {
    "zh": "◐ 二级 / 综合资料（中文维基百科）",
    "en": "◐ 二级 / 综合资料（英文维基百科）",
}


def export_to_obsidian(figure_name: str, cards: list[dict], angles: list[str]) -> Path:
    OBSIDIAN_FOLDER.mkdir(parents=True, exist_ok=True)

    sources_used = sorted({c.get("source_lang", "") for c in cards if c.get("source_lang")})
    sources_yaml = "\n".join(
        f'  - "{CREDIBILITY[lang]}"' for lang in sources_used if lang in CREDIBILITY
    )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # YAML frontmatter
    lines = [
        "---",
        f'title: "{figure_name}"',
        'type: 人物资料',
        'credibility: "◐ 二级来源"',
        "sources:",
        sources_yaml,
        f"tags: [人物, {figure_name}]",
        f"created: {today}",
        "---",
        "",
        f"# {figure_name} · 细节卡片",
        "",
    ]

    for i, card in enumerate(cards, 1):
        lang = card.get("source_lang", "")
        source_label = "中文维基" if lang == "zh" else "英文维基"
        flag = "🇨🇳" if lang == "zh" else "🇬🇧"
        keywords = card.get("keywords", [])

        lines.append(f"## 卡片 {i}　{flag} {source_label}")
        lines.append("")
        lines.append(card["detail"])
        lines.append("")
        if keywords:
            tags = " ".join(f"#{kw.replace(' ', '_')}" for kw in keywords)
            lines.append(f"**关键词** {tags}")
            lines.append("")

    lines += [
        "---",
        "",
        "# 写作切入角度",
        "",
    ]
    for angle in angles:
        lines.append(angle)
        lines.append("")

    output_path = OBSIDIAN_FOLDER / f"{figure_name}.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")

    return output_path
