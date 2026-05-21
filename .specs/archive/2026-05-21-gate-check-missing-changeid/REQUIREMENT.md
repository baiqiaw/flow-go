# REQUIREMENT — 2026-05-21-gate-check-missing-changeid

## 用户故事
作为 flow-go skill 的使用者（AI agent），我希望闸门检查脚本能正常调用，以便在阶段转换时自动验证工件完整性，而不是每次都回退到手动验证。

## 验收准则（BDD）

### AC-1 SKILL.md 闸门模板包含 --change-id
**Given**: SKILL.md 中第四步闸门检查的脚本化验证命令模板
**When**: AI agent 按模板调用 `python3 references/scripts/gate_check.py --stage <N> --specs-dir .specs/<id> --complexity <level> --change-id <id>`
**Then**: 脚本正常执行并返回检查结果（不再报 `--change-id` 必需参数错误）

### AC-2 3-develop.md auto-verify 包含 --change-id
**Given**: 3-develop.md 中 auto-verify 步骤的 l1-guard 调用模板
**When**: AI agent 按模板调用 `python3 references/scripts/gate_check.py --mode l1-guard --specs-dir .specs/<id> --project-dir . --change-id <id>`
**Then**: 脚本正常执行 l1-guard 检查

### AC-3 5-review.md blast-radius 包含 --change-id
**Given**: 5-review.md 中 blast-radius 验证步骤的调用模板
**When**: AI agent 按模板调用 `python3 references/scripts/gate_check.py --mode blast-radius --project-dir <项目根> --change-id <id>`
**Then**: 脚本正常执行 blast-radius 检查

## 非功能需求
- 性能：无影响（仅修改文档中的命令模板）
- 安全：无影响
- 兼容：完全向后兼容（添加参数不破坏现有功能）

## Out of Scope（范围排除）
- 不修改 gate_check.py 脚本本身
- 不修改 gate_artifacts.py / gate_blast.py / gate_l1.py / gate_l2.py 等子模块
- 不修改其他阶段文件（0/1/2/4/6/7 阶段不直接调用 gate_check.py）

## Principles（设计约束原则）
- 仅修改调用模板中的命令字符串，不改变脚本的调用语义
- 保持与 gate_check.py 当前 argparse 接口一致

## Key Decisions（关键决策记录）
- 无特殊决策，纯 bugfix 对齐
