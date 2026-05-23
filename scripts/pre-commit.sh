#!/usr/bin/env bash
# flow-go pre-commit hook
# 当 references/scripts/ 或 references/**/*.md 变更时运行回归测试

set -e

# 检查是否有相关文件变更
changed=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '^(references/scripts/.*\.py|references/.*\.md|tests/)' || true)

if [ -z "$changed" ]; then
    exit 0
fi

echo "📋 检测到 skill 相关文件变更，运行回归测试..."

# 查找可用的 python（优先 venv）
PYTHON=""
for candidate in "$VIRTUAL_ENV/bin/python3" "$HOME/venv/bin/python3" "$(which python3 2>/dev/null)"; do
    if [ -x "$candidate" ] && "$candidate" -m pytest --version &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -n "$PYTHON" ]; then
    "$PYTHON" -m pytest tests/ -q 2>&1 || {
        echo "❌ pytest 测试失败，commit 已阻止"
        exit 1
    }

    # 运行 skill 结构验证
    "$PYTHON" references/scripts/validate_skill.py --skill-dir . 2>&1 || {
        echo "❌ skill 结构验证失败，commit 已阻止"
        exit 1
    }
else
    echo "⚠️ 未找到安装了 pytest 的 python，跳过回归测试"
fi

echo "✅ 回归测试通过"
