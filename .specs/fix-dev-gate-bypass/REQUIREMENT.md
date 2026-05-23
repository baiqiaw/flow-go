# REQUIREMENT — fix-dev-gate-bypass

## 用户故事
作为使用 flow-go 流程的开发员，我希望测试失败时无法绕过、开发完成时必须提交代码和 SUMMARY.md，以避免质量问题被掩盖和阶段回退返工。

## 验收准则

### Bug1: 测试绕过修复
- **AC-1**: Given 3-develop.md 步骤 3 被执行，When 项目存在任何测试失败（无论是否本次变更导致），Then 开发被阻塞，必须修复后才能继续
- **AC-2**: Given 3-develop.md 步骤 9 verify 被执行，When verify 输出包含任何失败，Then 任务不被标记完成，禁止以"不是本次变更导致"为由绕过
- **AC-3**: Given anti-patterns.md 被加载，When 开发员自检 3-开发反模式，Then 能看到 dev-06（绕过非相关测试失败）条目

### Bug2: 过早完成修复
- **AC-4**: Given gate_artifacts.py 执行阶段 4 STANDARD/HEAVY 完整路径闸门，When specs 目录下无 `*-SUMMARY.md` 文件，Then 闸门检查失败，提示缺少任务摘要
- **AC-5**: Given gate_artifacts.py 执行阶段 4 任意复杂度路径，When `git diff HEAD --name-only` 有输出，Then 闸门检查失败，提示代码未提交
- **AC-6**: Given gate_artifacts.py 执行阶段 4，When specs 目录下有 `*-PROGRESS.md` 文件，Then 闸门检查失败，提示存在未完成任务
- **AC-7**: Given 3-develop.md 完成条件被检查，When 缺少"代码已提交"，Then 不能宣布开发阶段完成
- **AC-8**: Given anti-patterns.md 被加载，When 开发员自检 3-开发反模式，Then 能看到 dev-07（未提交代码就宣布完成）条目

## Key Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| "代码已提交"检查方式 | 检查工作区是否有未提交变更 | 确保所有代码变更已纳入版本控制 |
| 前置健康检查是否强制 | 是 | 用户明确要求：任何测试失败都是阻塞项 |
| SUMMARY.md 检查范围 | 中高复杂度路径 | 与闸门规则定义的复杂度等级一致 |

## 范围排除
- 不改动 gate-rules.md
- 不改动其他阶段的闸门逻辑
- 不新增配置项
- 不改动 gate_check.py 调度逻辑（仅传参）
