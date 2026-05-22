# SUMMARY — skills-borrow (T01-T09)

## 做了什么
借鉴 mattpocock/skills 8 项经验优化 flow-go 流程：新增 ADR/CONTEXT 模板、闸门脚本修复、4 个阶段文件增强（需求 CONTEXT 维护、设计 ADR+深模块+原型、任务垂直切片+AFK/HITL、开发结构化调试 6 Phase）、工件模板 mode 属性、SKILL.md 主调度更新，以及完整的回归测试验证。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/artifacts/memory-artifacts.md | 新增 | ADR + CONTEXT 两个模板文件 |
| references/artifacts/spec-artifacts.md | 修改 | 新增 ADR/CONTEXT 模板引用 |
| references/artifacts/task-artifacts.md | 修改 | 新增 mode 属性定义 |
| references/scripts/gate_check.py | 修改 | --complexity 大小写兼容 + ADR/CONTEXT 检查 |
| references/scripts/gate_artifacts.py | 修改 | 工件清单与 SKILL.md 对齐 |
| references/scripts/validate_state.py | 修改 | 输出格式统一 + 首行检查改用 errors |
| references/stages/0-requirement.md | 修改 | CONTEXT 自动维护 + 术语冲突检测 |
| references/stages/1-design.md | 修改 | ADR 三条件 + 深模块 + Seams + 原型子阶段 |
| references/stages/2-task.md | 修改 | 垂直切片 + AFK/HITL 标记 |
| references/stages/3-develop.md | 修改 | 6 Phase 结构化调试子流程 |
| SKILL.md | 修改 | CONTEXT/ADR 路由 + 闸门更新 + 原型路由 + AFK 调度 |

## Verify 输出
### 闸门脚本大小写一致性
```
$ diff <(gate_check.py --complexity HEAVY ...) <(gate_check.py --complexity heavy ...)
（无差异，大小写输出一致）
```

### 新增文件检查
```
$ test -f references/artifacts/memory-artifacts.md → 存在
$ grep "ADR" memory-artifacts.md → 6 匹配
$ grep "CONTEXT" memory-artifacts.md → 4 匹配
```

### 阶段文件关键词验证
```
0-requirement: CONTEXT.md → 6 处
1-design: 三条件 → 2 处, 深模块 → 1 处, Seams → 1 处, 原型 → 1 处
2-task: 垂直切片 → 4 处, AFK → 2 处, HITL → 3 处
3-develop: 反馈闭环 → 2 处, 可证伪 → 1 处, DEBUG- → 存在
```

### SKILL.md 一致性
```
$ grep CONTEXT.md SKILL.md → 5 处
$ grep adr/ SKILL.md → 存在
$ grep AFK SKILL.md → 存在
$ grep 原型 SKILL.md → 存在
```

### T09 闸门 verify
```
$ gate_check.py --stage 0 --complexity heavy → passed: true, missing: []
$ gate_check.py --stage 0 --complexity HEAVY → passed: true, missing: []
```

## 沿用既有抽象（grep 结果）
- 闸门脚本架构：沿用 gate_check.py 的 check_artifacts 分层 → 扩展
- 阶段文件结构：沿用 stages/*.md 的步骤编号风格 → 增量添加
- 工件模板格式：沿用 artifacts/*.md 的 Markdown 代码块模板 → 新增 memory-artifacts.md

## 越界检查
- TASK write_files：T01-T09 共声明 11 个目标文件
- 实际 diff 涉及：11 个文件（10 修改 + 1 新增）
- 越界：0

## 已知问题
- validate_state.py 的 per-change STATE.md 解析器不支持纯文本值格式（只支持 `- ` 列表和 `| ` 表格），非本次引入

## 交叉评审（独立子代理）
### 评审轮次: 2/3

### 第 1 轮结果
| 维度 | 结果 | 说明 |
|------|------|------|
| 规格合规 | PASS | 9 个任务 action/done 均已实现 |
| 设计对齐 | PASS | ADR/CONTEXT/深模块/Seams/原型/AFK 均按 DESIGN 实现 |
| 测试证据 | PASS | verify 命令真实执行，大小写一致性确认 |
| 边界卫生 | FAIL | gate_artifacts.py 阶段 0 与 SKILL.md 不一致 |
| 反幻觉 | PASS | 无虚构引用 |
| 质量底线 | FAIL | validate_state.py 2 处 bug + gate_check.py 1 处变量引用错误 |

### 第 1 轮修复
1. validate_state.py:224 — `missing.append()` 改为 `errors.append()`（missing 未定义）
2. validate_state.py:365 — `passed` 增加 `and len(errors) == 0`（忽略 errors 列表）
3. gate_check.py:182 — `args.specs_dir` 改为 `specs_dir`（本地变量已推导）
4. gate_artifacts.py:11 — `STANDARD_GATES[0]` 还原为 `[]`（与 SKILL.md 一致）

### 第 2 轮结果
| 维度 | 结果 | 说明 |
|------|------|------|
| 规格合规 | PASS | 4 个修复精确对应问题描述 |
| 设计对齐 | PASS | 修复遵循原有架构 |
| 测试证据 | PASS | 脚本正常运行，变量引用正确 |
| 边界卫生 | PASS | 修复范围严格限定在 3 个问题文件 |
| 反幻觉 | PASS | 所有引用变量/函数均有定义 |
| 质量底线 | PASS | 未引入新 bug |

### 评审结论
6 维全 PASS，交叉评审通过。
