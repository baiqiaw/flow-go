# DESIGN — fix-dev-gate-bypass

## 0. 变更概述

修复 3-开发阶段两重门禁缺陷：测试绕过（Bug1）和过早完成（Bug2）。

## 1. 受影响模块

### Bug1: 测试绕过修复

**文件**：`references/stages/3-develop.md`

**改动**：
- 步骤 3：移除"已有问题"概念，前置健康检查从"可选"改为强制
- 步骤 9：verify 增加"0 失败"强制要求，禁止区分失败来源
- 完成条件：增加"代码已提交"

**文件**：`references/anti-patterns.md`

**改动**：新增 dev-06（绕过非相关测试失败）和 dev-07（未提交代码就宣布完成）

### Bug2: 过早完成修复

**文件**：`references/scripts/gate_artifacts.py`

**改动**：
- 新增 `import glob, subprocess`
- `check_artifacts()` 新增 `project_dir=None` 参数（向后兼容）
- 阶段 4 增加三项检查：
  1. SUMMARY.md：glob `*-SUMMARY.md`（仅 STANDARD/HEAVY 完整/增量路径）
  2. 代码已提交：`git diff --name-only HEAD`（所有复杂度）
  3. PROGRESS 残留：glob `*-PROGRESS.md`（所有复杂度）

**文件**：`references/scripts/gate_check.py`

**改动**：传递 `project_dir` 给 `check_artifacts()`

## 2. 数据流

```
用户 go → flow-go 路由 → 闸门检查 gate_check.py
  → check_artifacts(stage=4, project_dir=.)
    → glob *-SUMMARY.md → 检查存在性
    → git diff --name-only HEAD → 检查代码已提交
    → glob *-PROGRESS.md → 检查无中断任务
  → 返回 {passed, missing, warnings}
→ 不通过 → 停下提示
→ 通过 → 进入 4-测试阶段
```

## 3. Key Decisions

| 决策 | 选择 | 理由 | 三条件评估 |
|------|------|------|-----------|
| 前置健康检查是否强制 | 是 | 用户明确要求任何测试失败都是阻塞项 | 不创建 ADR |
| 代码提交检查方式 | 检查工作区未提交变更 | 确保代码纳入版本控制 | 不创建 ADR |
| check_artifacts 新参数 | project_dir=None（向后兼容） | 不影响已有调用方 | 不创建 ADR |
| SUMMARY.md 检查范围 | 中高复杂度路径 | 与 gate-rules.md 保持一致 | 不创建 ADR |

## 4. 风险清单

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| subprocess git 调用性能 | 低 | 低 | 小仓库 <100ms |
| glob 匹配非预期文件 | 低 | 低 | 命名约定已规范 |
| git 命令不存在 | 低 | 中 | 捕获异常，输出 warning |

## 5. 既有架构对齐

- 触碰模块：gate_artifacts.py、gate_check.py
- 禁动清单：不改动 gate_l1/l2/l3、blast radius 模块
- 沿用决策：返回结构不变，新增参数有默认值

## 6. 深模块评估

- gate_artifacts.py 的 `check_artifacts()` 接口从 4 参数扩展到 5 参数（新增 project_dir），接口面积增长有限
- 新增的 stage 4 检查逻辑全部封装在 `check_artifacts()` 内部，不暴露新接口
- 结论：无过度抽象，无需引入新的 Seam
