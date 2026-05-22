# UAT — CH-20260522-001

## 验收日期
- 2026-05-22

## AC 验收结果
| AC | 结果 | 证据 |
|---|---|---|
| AC-1 规则外置到独立文件 | PASS | gate-rules.md 存在，SKILL.md 481→440 行（减 41 行） |
| AC-2 反模式清单原子化 | PASS | 38 条反模式全部有 `[阶段-序号-关键词]` id |
| AC-3 闸门检查结构化输出 | PASS | gate_check.py --structured-output 参数生效 |
| AC-4 gate_check.py 按类别检查 | PASS | gate_check.py --categories 参数生效 |
| AC-5 架构原则注入进化机制 | PASS | 5 项原则（原子化/结构化/关注点分离/单一职责/可组合）在 evolution_reflect.py 中 |

## 非功能需求
- 性能：gate-rules.md grep 按需加载 ✅
- 安全：HARD-GATE 语义保留在 SKILL.md ✅
- 兼容：不传新参数时行为不变 ✅

## 改动文件清单
| 文件 | 变更类型 |
|------|---------|
| SKILL.md | 修改（闸门表+角色约束+反模式→引用替换） |
| references/gate-rules.md | 新增 |
| references/anti-patterns.md | 修改（添加 38 条原子化 id） |
| references/scripts/gate_check.py | 修改（+--categories +--structured-output） |
| references/scripts/evolution_reflect.py | 修改（+ARCHITECTURE_PRINCIPLES +_detect_architecture_violations） |

## 验收结论
5/5 AC 满足，非功能需求达标。验收通过。
