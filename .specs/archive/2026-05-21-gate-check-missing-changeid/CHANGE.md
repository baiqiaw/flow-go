# CHANGE — 2026-05-21-gate-check-missing-changeid

## Why（为什么做）
`gate_check.py` 在 `state-parallel` change 中新增了 `--change-id` 必需参数，但 SKILL.md、3-develop.md、5-review.md 中的闸门调用模板未同步更新，导致实际使用时闸门脚本报参数错误，每次都回退到手动验证。

## What（做什么）
修复 3 处 gate_check.py 调用模板，补上缺失的 `--change-id` 参数：
1. SKILL.md 第四步闸门检查的脚本化验证命令模板
2. 3-develop.md auto-verify 步骤的 l1-guard 调用
3. 5-review.md blast-radius 步骤的调用

## 影响面
- 涉及模块：SKILL.md、references/stages/3-develop.md、references/stages/5-review.md
- 数据库变更：否
- API 变更：否
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- 不修改 gate_check.py 本身（脚本行为正确，是调用方模板的问题）
- 不修改其他未引用 gate_check.py 的阶段文件
- 不改动 gate_artifacts.py / gate_blast.py 等子模块

## 验收线
3 处调用模板均包含 `--change-id` 参数，闸门脚本可正常执行（不再因缺少参数报错）。

## 路径建议
最短路径，理由：3 处纯文本修改（文档型变更），无代码逻辑改动，无架构影响。
