# UAT — live-qa-acceptance

## 验收脚本
### UAT-1 AC-1 活体验证步骤
- 前置条件：7-acceptance.md 已更新
- 步骤：grep "步骤 1LV" + 验证 5 个子步骤完整
- 预期：1LV-1~1LV-5 子步骤存在，格式一致
- 结果：✅ 4 处匹配，子步骤完整

### UAT-2 AC-2 不可运行场景处理
- 前置条件：7-acceptance.md 已更新
- 步骤：grep 验证 web/cli/library/unknown 分级处理
- 预期：4 种分级分支存在
- 结果：✅ 4 处匹配

### UAT-3 AC-3 Bug 修复循环
- 前置条件：7-acceptance.md 已更新
- 步骤：grep 验证 1BF-1~1BF-5 子步骤存在
- 预期：角色切换 + 逐个修复 + 原子提交 + 重验
- 结果：✅ 5 处匹配，含角色切换声明和开发员红线

### UAT-4 AC-4 修复循环自调节
- 前置条件：7-acceptance.md 已更新
- 步骤：grep 验证 3 轮/>5 个阈值
- 预期：自调节检查和停下报告存在
- 结果：✅ 3 处匹配

### UAT-5 AC-5 验收重验
- 前置条件：7-acceptance.md 已更新
- 步骤：grep 验证 1RR-1~1RR-3 子步骤
- 预期：全量重走 + 结果判定 + 完成记录
- 结果：✅ 3 处匹配

### UAT-6 AC-6 UAT.md 模板增强
- 前置条件：deploy-artifacts.md 已更新
- 步骤：grep 验证 LV-NN/Bug 清单/RR-NN 章节
- 预期：3 个新章节在验收脚本之后、健康评分之前
- 结果：✅ 章节顺序正确：验收脚本 → 活体验证 → 验收重验 → 健康评分

### UAT-7 AC-7 闸门规则更新
- 前置条件：gate-rules.md 已更新
- 步骤：grep 验证 3 条路径活体验证条款
- 预期：完整/最短/增量 3 条路径条件已更新
- 结果：✅ 3 处匹配

### UAT-8 AC-8 SKILL.md 更新
- 前置条件：gate-rules.md 已更新
- 步骤：grep 确认 SKILL.md 无硬编码条件
- 预期：SKILL.md 中无 7-验收入口/完成条件文本
- 结果：✅ 无匹配（间接引用 gate-rules.md）

## 活体验证
**项目类型**：library（流程框架，markdown + Python 脚本）
**验证方式**：测试输出（pytest 26 项 + gate_check.py）
**应用状态**：跳过（纯库无应用入口，通过测试套件验证）

### 活体验证清单
| 编号 | 路径/操作 | 预期结果 | 实际结果 | 状态 | 证据 |
|------|----------|---------|---------|------|------|
| LV-01 | pytest 26 项回归测试 | 全部 PASSED | 26/26 PASSED | ✅ | pytest output |
| LV-02 | gate_check.py stage 7 验证 | passed=true | passed=true | ✅ | JSON output |
| LV-03 | gate-rules.md 活体验证条款 grep | 3 处匹配 | 3 处匹配 | ✅ | grep 输出 |
| LV-04 | 7-acceptance.md 新步骤 grep | 1LV/1BF/1RR 存在 | 4 处匹配 | ✅ | grep 输出 |
| LV-05 | SKILL.md 无硬编码验证 | 0 匹配 | 0 匹配 | ✅ | grep exit code 1 |

### Bug 清单
无 Bug 发现。Critical/High 合计 = 0。

## 验收重验
**重验次数**：0（无 Critical/High Bug，跳过验收重验步骤）

## 健康评分（health_scorer.py 输出）
| 维度 | 分数 | 权重 | 加权 |
|------|------|------|------|
| AC 通过率 | 100 | 30% | 30 |
| 测试覆盖 | 100（26/26 passed） | 20% | 20 |
| 评审效率 | 100（0 严重项） | 15% | 15 |
| 代码质量 | 100（6/6 R 维度 PASS） | 15% | 15 |
| 边界卫生 | 100（3 文件 = TASK 范围） | 15% | 15 |
| 文档完备 | 100（8/8 工件齐全） | 5% | 5 |
**综合评分**：100 / 100（A级）

## 验收签字
- 产品经理：✅ 8/8 AC 全部通过，活体验证 5/5 通过，无 Critical/High Bug
- 项目经理：✅ 所有工件齐全，回归测试 26/26 通过，闸门检查通过

## LESSONS 提名
| 编号 | 场景 | 教训 | 提名人 |
|------|------|------|--------|
| — | — | 本 change 流程顺畅，无显著失败经验需提名 | — |

## 归档
- 归档路径：.specs/archive/2026-05-24-live-qa-acceptance/
- 归档时间：2026-05-24
