# SUMMARY — 进化系统自优化

## 做了什么
优化 flow-go 自我进化系统 7 个薄弱点，使其在新项目中也能正常触发。

## AC 达成

| AC | 内容 | 状态 |
|----|------|------|
| AC-1 | 归档自检 3 项进化检查 | ✅ special-flows.md 自检清单 |
| AC-2 | 健康评分自动计算 | ✅ special-flows.md 步骤 4.3 |
| AC-3 | 信号检测模糊匹配 | ✅ evolution_signal.py 4 个提取器 |
| AC-4 | CAPTURE 路径闭环 | ✅ 1-design.md 步骤 0 |
| AC-5 | BITTER PILL 自动发现 | ✅ _path_utils.py + bitter_pill_audit.py |
| AC-6 | 新项目首次进化 | ✅ SKILL.md FIX 条件 3 + special-flows.md 首次进化检测 |
| AC-7 | 轻量会话内进化 | ✅ SKILL.md 轻量进化检查 |

## 改动文件
- SKILL.md (+10 行)
- references/scripts/_path_utils.py (+38 行)
- references/scripts/bitter_pill_audit.py (+8 行)
- references/scripts/evolution_signal.py (+23 行)
- references/stages/1-design.md (+5 行)
- references/stages/special-flows.md (+18 行)

## 验证闭环
- 功能不变 ✅（未改变任何现有进化路径的行为）
- verify ✅（9/9 脚本导入通过，bitter_pill 无参数运行通过，validate_skill 通过）
