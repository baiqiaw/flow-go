# SUMMARY — 2026-05-21-gate-check-missing-changeid

## 修改内容
修复 3 处 gate_check.py 调用模板，补上缺失的 `--change-id` 必需参数：

1. **SKILL.md 第 209 行**：闸门脚本化验证命令模板 → 补上 `--change-id <id>`
2. **3-develop.md 第 32 行**：auto-verify l1-guard 调用 → 补上 `--change-id <id>`
3. **5-review.md 第 19 行**：blast-radius 验证调用 → 补上 `--change-id <id>`

## 修改文件
| 文件 | 改动类型 |
|------|---------|
| SKILL.md | 命令模板加 `--change-id <id>` |
| references/stages/3-develop.md | 命令模板加 `--change-id <id>` |
| references/stages/5-review.md | 命令模板加 `--change-id <id>` |

## 验证结果
| AC | 验证命令 | 结果 |
|----|---------|------|
| AC-1 | `gate_check.py --stage 1 --change-id <id> --specs-dir .specs/<id> --complexity standard` | passed: true |
| AC-2 | 3-develop.md 模板已包含 `--change-id`（文本验证） | ✅ |
| AC-3 | `gate_check.py --mode blast-radius --change-id <id> --project-dir .` | 正常执行，exceeded: false |

## 交叉评审
LITE 复杂度跳过独立交叉评审。
