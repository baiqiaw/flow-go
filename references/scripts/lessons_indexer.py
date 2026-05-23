#!/usr/bin/env python3
"""LESSONS 索引器 — 从 LESSONS.md 生成 .lessons.jsonl 机器可读索引

用法：
    python3 lessons_indexer.py .specs/LESSONS.md
    python3 lessons_indexer.py .specs/LESSONS.md --output .specs/.lessons.jsonl
    python3 lessons_indexer.py .specs/LESSONS.md --search "migration"
"""

import argparse
import json
import re
import sys


def parse_lessons(content):
    """从 LESSONS.md 解析条目列表"""
    entries = []
    pattern = re.compile(
        r'###\s+(L-\d+)\s+(.+?)\n'
        r'(.*?)(?=###\s+L-|\Z)',
        re.DOTALL,
    )
    for m in pattern.finditer(content):
        entry_id = m.group(1)
        title = m.group(2).strip()
        body = m.group(3)

        def extract_field(name):
            p = re.compile(r'\*\*' + name + r'\*\*[：:]\s*(.+?)(?:\n|$)')
            found = p.search(body)
            return found.group(1).strip() if found else ""

        entry = {
            "id": entry_id,
            "title": title,
            "keywords": [k.strip() for k in extract_field("触发关键词").split("/") if k.strip()],
            "scenario": extract_field("场景"),
            "lesson": extract_field("教训"),
            "status": extract_field("状态") or "active",
            "source": extract_field("提名来源"),
            "date": extract_field("日期"),
        }
        entries.append(entry)
    return entries


def search_lessons(entries, query):
    """按关键词搜索 lessons"""
    results = []
    q = query.lower()
    for e in entries:
        if (
            q in e["title"].lower()
            or q in e["scenario"].lower()
            or q in e["lesson"].lower()
            or any(q in k.lower() for k in e["keywords"])
        ):
            results.append(e)
    return results


def main():
    parser = argparse.ArgumentParser(description="LESSONS 索引器")
    parser.add_argument("input", help="LESSONS.md 文件路径")
    parser.add_argument("--output", help="输出 JSONL 路径（默认 .lessons.jsonl）")
    parser.add_argument("--search", help="搜索关键词")
    args = parser.parse_args()

    try:
        with open(args.input, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：文件不存在 — {args.input}", file=sys.stderr)
        sys.exit(1)

    entries = parse_lessons(content)

    if args.search:
        results = search_lessons(entries, args.search)
        if results:
            for r in results:
                print(f"{r['id']}: {r['title']}")
                print(f"  教训: {r['lesson']}")
                print(f"  状态: {r['status']}")
                print()
        else:
            print(f"未找到匹配 '{args.search}' 的条目")
        return

    output_path = args.output or os.path.join(os.path.dirname(os.path.abspath(args.input)), ".lessons.jsonl")
    with open(output_path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"已索引 {len(entries)} 条到 {output_path}")


if __name__ == "__main__":
    main()
