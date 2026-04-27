import sys
import db
import fetch
import analyze
import export


def main():
    if len(sys.argv) < 2:
        print("用法: python main.py <人物名称>")
        print("示例: python main.py 居里夫人")
        sys.exit(1)

    figure_name = sys.argv[1].strip()
    db.init_db()

    print(f"\n正在搜索「{figure_name}」的资料...\n")

    zh_text = fetch.fetch_wikipedia(figure_name, "zh")
    en_text = fetch.fetch_wikipedia(figure_name, "en")

    if not zh_text and not en_text:
        print(f"❌ 未能找到「{figure_name}」的维基百科资料。")
        print("   请检查人物姓名拼写，或尝试中英文名称。")
        sys.exit(1)

    sources = []
    if zh_text:
        sources.append("中文维基百科")
    if en_text:
        sources.append("英文维基百科")
    print(f"✓ 已获取资料来源：{' + '.join(sources)}\n")

    print("正在提取细节卡片...\n")
    cards = analyze.extract_detail_cards(figure_name, zh_text, en_text)

    if not cards:
        print("⚠ 未能提取到细节卡片，请稍后重试。")
        sys.exit(1)

    db.save_cards(figure_name, cards)

    print("─" * 60)
    print(f"  {figure_name} · 细节卡片")
    print("─" * 60)

    for i, card in enumerate(cards, 1):
        lang = card.get("source_lang", "")
        flag = "🇨🇳" if lang == "zh" else "🇬🇧"
        source_label = "中文维基" if lang == "zh" else "英文维基"
        keywords = card.get("keywords", [])
        keywords_str = "  🔍 " + " · ".join(keywords) if keywords else ""

        print(f"\n【卡片 {i}】{flag} [{source_label}]")
        print(card["detail"])
        if keywords_str:
            print(keywords_str)

    print("\n" + "─" * 60)
    print("  写作切入角度")
    print("─" * 60 + "\n")

    angles = analyze.generate_narrative_angles(figure_name, cards)
    for angle in angles:
        print(angle)

    print(f"\n✓ 已保存 {len(cards)} 张卡片到本地数据库\n")

    output_path = export.export_to_obsidian(figure_name, cards, angles)
    print(f"✓ 已导出到 Obsidian：{output_path}\n")


if __name__ == "__main__":
    main()
