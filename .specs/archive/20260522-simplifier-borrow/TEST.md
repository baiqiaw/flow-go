# TEST — simplifier-borrow

## 测试策略
config 类型变更，验证方式为 grep 内容检查 + 结构完整性确认。

## 测试结果

| AC | 测试项 | 预期 | 实际 | 结果 |
|----|--------|------|------|------|
| AC-1 | 精炼环章节存在 | `阶段内精炼环` 在 SKILL.md | 找到 | PASS |
| AC-1 | 精炼环引用在 3-develop.md | `精炼环` 在 reference | 找到 2 处 | PASS |
| AC-2 | 增量闸门段落存在 | `增量闸门模式` 在 SKILL.md | 找到 | PASS |
| AC-3 | 首要原则列存在 | `首要原则（必须保护）` 在 SKILL.md | 找到 | PASS |
| AC-3 | 6 个角色全覆盖 | 角色约束表含 6 行 | 6 行 | PASS |
| AC-4 | LITE 不可跳过 ≥3 条 | 3 条场景 | 3 条 | PASS |
| AC-4 | SUGGEST 不可自动执行 ≥3 条 | 4 条症状 | 4 条 | PASS |
| AC-5 | 反模式章节存在 | `阶段反模式速查` 在 SKILL.md | 找到 | PASS |
| AC-5 | 3-开发反模式 ≥4 条 | 5 条 | 5 条 | PASS |
| AC-5 | 4-测试反模式 ≥4 条 | 4 条 | 4 条 | PASS |
| AC-5 | 5-审查反模式 ≥4 条 | 4 条 | 4 条 | PASS |
| AC-5 | reference 引用 | 3 个文件有反模式引用 | 全找到 | PASS |
| AC-6 | 验证闭环章节存在 | `阶段内验证闭环` 在 SKILL.md | 找到 | PASS |
| AC-6 | 3-develop.md 引用 | `验证闭环` 在 reference | 找到 2 处 | PASS |
| AC-6 | 5-review.md 引用 | `验证闭环` 在 reference | 找到 3 处 | PASS |

## 结构完整性
- 7 步主流程结构未变 ✅
- HARD-GATE 机制未绕过 ✅
- Skill 链式调用白名单未扩展 ✅
- LITE/STANDARD/HEAVY 三级兼容 ✅

## 健康评分
94/100（-6：增量闸门未脚本化，留后续 change）
