# SUMMARY — live-qa-acceptance

## 改动文件
| 文件 | 变更 | 任务 |
|------|------|------|
| references/artifacts/deploy-artifacts.md | +23 行（UAT 模板新增活体验证 + 验收重验章节） | T01 |
| references/gate-rules.md | +6/-2 行（3 条路径 7-验收闸门条件追加活体验证条款） | T03 |
| references/stages/7-acceptance.md | +67/-16 行（新增 1LV/1BF/1RR 步骤，原步骤重编号 4-11，更新自检/入口/完成/上下文/中断恢复） | T02 |

## verify 输出
### T01
```
$ grep -c "## 活体验证" references/artifacts/deploy-artifacts.md
2
$ grep -c "## 验收重验" references/artifacts/deploy-artifacts.md
1
$ grep -c "Bug 清单" references/artifacts/deploy-artifacts.md
2
```

### T03
```
$ grep -c "活体验证全通过或已跳过" references/gate-rules.md
3
$ ! grep -q "7-验收.*入口条件\|7-验收.*完成条件" SKILL.md
SKILL.md 无硬编码 ✅
```

### T02
```
$ grep -c "步骤 1LV\|步骤 1BF\|步骤 1RR" references/stages/7-acceptance.md
4
$ grep -c "活体验证已执行或已跳过" references/stages/7-acceptance.md
1
```

## 自检
- [x] 功能不变：原有步骤行为未改变，仅新增步骤和重编号
- [x] 反模式清零：无 scope creep / 无新依赖 / 无硬编码
- [x] 精炼环通过
- [x] 验证闭环：verify 全通过 ✅ / diff 边界 ✅
- [x] 未改 REQUIREMENT / DESIGN
- [x] SKILL.md 确认无硬编码 7-验收条件

## AC 覆盖
| AC | 任务 | 验证 |
|----|------|------|
| AC-1 活体验证步骤 | T02 (1LV-1~1LV-5) | grep 验证步骤存在 |
| AC-2 不可运行场景处理 | T02 (1LV-2 分级处理) | grep 验证 web/cli/library/unknown 分支 |
| AC-3 Bug 修复循环 | T02 (1BF-1~1BF-5) | grep 验证步骤存在 |
| AC-4 修复循环自调节 | T02 (1BF-3/1BF-4) | grep 验证阈值和停下报告 |
| AC-5 验收重验 | T02 (1RR-1~1RR-3) | grep 验证步骤存在 |
| AC-6 UAT.md 模板增强 | T01 | grep 验证 LV-NN/Bug 清单/RR-NN 章节 |
| AC-7 闸门规则更新 | T03 | grep 验证 3 条路径条件更新 |
| AC-8 SKILL.md 更新 | T03 (间接) | grep 验证 SKILL.md 无硬编码 |

## 交叉评审
### 评审矩阵（矩阵 B — 代码评审）
| 维度 | 结果 | 说明 |
|------|------|------|
| 规格合规 | PASS | 3 个文件变更完全对齐 TASK action/done |
| 设计对齐 | PASS | 实现严格遵循 DESIGN 方案，编号/分级/阈值/模板逐项一致 |
| 测试证据 | PASS | grep verify 输出真实，目标在 diff 中有对应内容 |
| 边界卫生 | PASS | diff 恰好 3 个文件 = TASK write_files，无越界 |
| 反幻觉 | PASS | 所有引用路径为已有文件，无虚构依赖 |
| 质量底线 | PASS | 步骤跳转引用自洽，编号链路无断裂 |

### 发现问题
无
