import json
import os
from openai import OpenAI

MODEL = "claude-sonnet-4-6"


def _client() -> OpenAI:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY 环境变量未设置。\n"
            "请运行: export ANTHROPIC_API_KEY=your_key"
        )
    return OpenAI(api_key=api_key, base_url="https://api.anthropic.com/v1/")


def extract_detail_cards(figure_name: str, zh_text: str | None, en_text: str | None) -> list[dict]:
    parts = []
    if zh_text:
        parts.append(f"=== 中文维基百科 ===\n{zh_text[:6000]}")
    if en_text:
        parts.append(f"=== English Wikipedia ===\n{en_text[:6000]}")
    combined = "\n\n".join(parts)

    prompt = f"""你是一位擅长发现历史女性内在世界的研究者，为写作者提供创作素材。

请阅读以下关于"{figure_name}"的维基百科资料，从中提取 5–8 张"细节卡片"。

【细节卡片的标准】
- 具体、感官性的瞬间，而非概括性评价
- 压力下的选择、沉默的时刻、关系的细节
- 让读者感受到"这是一个真实的人"的内容
- 避免：生卒年月罗列、履历式的成就清单

请以 JSON 数组格式返回，每张卡片包含：
- "detail": 细节描述（100–200字，中文）
- "source_lang": "zh" 或 "en"（该细节主要来源）
- "keywords": 2–4个关键词，用于图片搜索（如 ["实验室", "1898年", "镭"]）

只返回 JSON 数组，不要添加任何解释文字。

资料如下：
{combined}"""

    response = _client().chat.completions.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]

    try:
        cards = json.loads(raw)
        if isinstance(cards, list):
            return cards
    except Exception:
        pass

    return []


def generate_narrative_angles(figure_name: str, cards: list[dict]) -> list[str]:
    card_text = "\n".join(
        f"- {c['detail']} [来源: {'中文维基' if c.get('source_lang') == 'zh' else '英文维基'}]"
        for c in cards
    )

    prompt = f"""你是一位写作导师，专注于帮助作者找到切入历史女性故事的角度。

以下是关于"{figure_name}"的细节卡片：

{card_text}

请根据这些细节，为写作者提供 2–3 个差异化的写作切入角度。

【要求】
- 每个角度情感基调不同（例如：亲密/私人视角、结构/历史视角、反常/颠覆视角）
- 每个角度 2–3 句话，说明从何处进入、能带给读者什么体验
- 用中文写作，语气像在和作者朋友对话
- 格式：1. / 2. / 3. 编号列表

只返回编号列表，不要前言和总结。"""

    response = _client().chat.completions.create(
        model=MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content.strip()
    angles = []
    for line in raw.split("\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("-")):
            angles.append(line)

    return angles if angles else [raw]
