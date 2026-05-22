# Gate Rules — 闸门检查与角色约束

> 从 SKILL.md 外置的规则文件。按分类标签组织，支持 `--categories` 按需加载。
> 分类：gate（闸门前置）/ role（角色约束）/ safety（安全场景）

---

## 1. 闸门检查规则 [gate]

| 进入阶段 | 必须存在（STANDARD/HEAVY） | LITE 简化闸门 | 缺失时 |
|---|---|---|---|
| 0-需求 | 无 | 同 STANDARD | 直接进 |
| 1-设计 | CHANGE.md + REQUIREMENT.md + `<change-id>-REVIEW.md`（需求评审 PASS） | LITE 跳过此阶段 | 提示先跑 0-需求 |
| 2-任务 | REQUIREMENT.md + DESIGN.md + `<change-id>-REVIEW.md`（设计评审 PASS） | LITE 跳过此阶段 | 提示先跑 1-设计 |
| 3-开发 | DESIGN.md + TASK.md（含 verify）+ `<change-id>-REVIEW.md`（任务评审 PASS）；指定任务时验证该任务存在且 depends_on 已完成 | CHANGE.md（含内联 AC） | 提示先跑 2-任务 |
| 4-测试 | 代码已提交 + SUMMARY.md（含交叉评审 PASS） | 代码已提交 | 提示先跑 3-开发 |
| 5-审查 | TEST.md + 全部 SUMMARY | LITE 跳过此阶段 | 提示先跑 4-测试 |
| 6-部署 | REVIEW.md（严重项经循环评审确认 = 0） | LITE 跳过此阶段 | 提示先跑 5-审查 |
| 7-验收 | DEPLOY.md + 全部工件 | 4-测试通过 + CHANGE.md AC 全部满足 | 提示先跑 6-部署 |

**闸门脚本化验证**：`python3 references/scripts/gate_check.py --stage <N> --change-id <id> --specs-dir .specs/<id> --complexity <level> [--categories gate]`

---

## 2. LITE 安全场景 [safety]

LITE 不可跳过的 3 种场景（即使 LITE 也必须走完整闸门）：
1. 涉及安全相关代码（认证/授权/加密/数据隔离）
2. 改动跨 ≥3 个模块的公共接口
3. 包含数据迁移或数据格式变更

---

## 3. 角色约束规则 [role]

| 角色 | 首要原则（必须保护） | 禁止（绝对不做） |
|---|---|---|
| 产品经理 | 需求忠实于用户意图 | 写实现代码、改技术设计 |
| 技术经理 | 架构一致性 | 设计阶段写实现代码；审查阶段自己改代码 |
| 项目经理 | 需求完整传递到任务 | 改需求内容、改技术设计 |
| 开发员 | 功能对齐 DESIGN.md | 改 REQUIREMENT/DESIGN、跨任务改动 |
| 测试员 | 用例忠实于 REQUIREMENT AC | 自己修代码、删除/弱化失败用例 |
| 运维 | 部署安全性与可回滚性 | 改业务代码、未经审查直接部署 |

---

## 4. 阶段反模式速查 [antipattern]

> 完整反模式清单见 `references/anti-patterns.md`（每条有原子化 id，可脚本化检查）。
> 以下为 SKILL.md 原内联摘要，供快速自检。

### 3-开发 反模式
- 在 TASK.md write_files 范围外修改文件（scope creep）
- 引入 DESIGN.md 未规划的新依赖
- 硬编码本应配置化的值（端口/URL/密钥）
- 跳过错误处理"因为场景太简单不会出错"
- 在 LITE 模式下合并多个 task 的改动到一个 commit

### 4-测试 反模式
- 只测 happy path，跳过边界和异常
- 测试代码与实现代码紧耦合（mock 过深导致测试失去价值）
- 删除或弱化失败的测试用例而非修复实现
- 测试依赖执行顺序（用例间有隐式依赖）

### 5-审查 反模式
- 只审查自己写的代码（违反独立性）
- 审查同时修改代码（违反技术经理红线）
- 跳过跨模块影响分析（"只改了一个文件"）
- 审查报告只有"通过"无具体检查记录
