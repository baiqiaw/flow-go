# DESIGN — state-parallel

## 0. 技术栈选定
| 候选 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| A. 索引+分离：STATE.md 索引表 + .specs/\<id\>/STATE.md | 真文件隔离无冲突；保持 STATE.md 入口地位；改动最小 | 需读两个文件 | **首选** |
| B. 单文件多段 | 单文件简单 | 两会话写同一文件有冲突风险 | 备选 |
| C. JSON 状态文件 | 机器友好 | 破坏 markdown 风格；全部重写 | 排除 |

最终选择：A，理由：唯一能实现真并行无冲突的方案，与现有 .specs/\<id\>/ 目录天然对齐。

## 1. 架构图

### Before（当前）
```
STATE.md（单文件，全量状态）
├── 活跃 Change: "xxx"
├── 当前阶段: "3-开发"
├── 当前任务: "T01"
├── 中断任务: 无
├── Pipeline 待续: 无
├── 并行 Change: 无
├── 阶段进度: "步骤 5: xxx"
└── 更新时间: 2026-05-21
         ↑
    所有会话读写同一文件 ← 冲突！
```

### After（新设计）
```
STATE.md（项目级索引，仅读/低频写）
├── 活跃 Change 表:
│   | change-id      | 阶段   | 最后更新   |
│   | state-parallel | 1-设计 | 2026-05-21 |
├── Pipeline 待续
└── 更新时间

         ↓ 每个会话只读写自己的 change state

.specs/<id>/STATE.md（change 级详细状态，高频读写）
├── 当前阶段
├── 当前任务
├── 中断任务
├── 阶段进度
└── 更新时间
```

### 数据流
```
会话启动 → 读 STATE.md（索引）
  ├─ 活跃 Change 数 = 0 → 0-需求（新 change）
  ├─ 活跃 Change 数 = 1 → 自动读 .specs/<id>/STATE.md → 路由
  └─ 活跃 Change 数 > 1 → 列表让用户选 → 读选中 change 的 STATE.md → 路由

阶段推进 → 只写 .specs/<id>/STATE.md（阶段/任务/进度）
阶段转换 → 同时更新 STATE.md 索引表的该 change 行（低频）
归档 → 从 STATE.md 索引表移除该行 + 删除 .specs/<id>/STATE.md
```

## 2. 数据流

### 会话启动数据流
1. 读 STATE.md → 解析活跃 Change 表
2. 表空 → 新 change 流程
3. 表有 1 行 → 自动读 `.specs/<id>/STATE.md` → 路由到当前阶段
4. 表有多行 → AskUserQuestion 让用户选 → 读选中的 STATE.md → 路由

### 状态更新数据流
- **阶段内高频更新**（阶段进度、当前任务）：只写 `.specs/<id>/STATE.md`
- **阶段转换**（阶段变更）：写 `.specs/<id>/STATE.md` + 更新 STATE.md 索引表对应行
- **启动/归档**（增删 change）：写 STATE.md 索引表 + 创建/删除 per-change STATE

### 旧格式迁移数据流
1. 检测：STATE.md 中 `活跃 Change` 值为非表格的单行文本（非"无"）
2. 读取旧字段：活跃 Change、当前阶段、当前任务、中断任务、阶段进度
3. 生成新 STATE.md（表格格式，迁移后的索引行）
4. 创建 `.specs/<id>/STATE.md`（迁移后的详细状态）
5. 保留旧内容为注释（备份）

## 3. API 设计

### STATE.md 索引表 Schema
```markdown
## 活跃 Change
| change-id | 阶段 | 最后更新 |
|-----------|------|---------|
| xxx       | N-名称 | YYYY-MM-DD |
```

### .specs/\<id\>/STATE.md Schema
```markdown
# CHANGE STATE — <change-id>

## 当前阶段
- N-名称

## 当前任务
- T01-xxx / 无

## 中断任务
- T02-xxx / 无

## 阶段进度
- 步骤 N: 描述 / 无

## 更新时间
- YYYY-MM-DD
```

### 迁移检测规则
```python
def is_old_format(state_content: str) -> bool:
    """旧格式：活跃 Change 字段值为单行文本（非表格、非'无'）"""
    # 正则匹配 ## 活跃 Change 后的非表格内容
    # 返回 True 表示需要迁移
```

### Stage 读写流程（模板化）

每个 stage 文件在新格式下的标准读写路径：

**读路径**（会话已选定 change-id）：
1. 读 `.specs/<change-id>/STATE.md` → 获取当前阶段、当前任务、阶段进度
2. 闸门检查时：gate_check.py 接收 `--change-id` 参数 → 读同一文件获取阶段信息

**写路径**：
1. 阶段内步骤完成 → 写 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段
2. 阶段转换 → 写 `.specs/<change-id>/STATE.md` 的 `当前阶段` + 更新 STATE.md 索引表对应行
3. 任务开始/完成 → 写 `.specs/<change-id>/STATE.md` 的 `当前任务` 字段

**change-id 传递**：
- SKILL.md 第一步读状态时确定 change-id，写入会话上下文
- 后续所有阶段文件通过会话上下文获取 change-id（不重新读索引）
- 脚本通过 `--change-id` 参数获取

## 4. ADR

### ADR-001 索引格式：Markdown 表格
- 背景：STATE.md 需展示多个活跃 change 概要
- 选项：A) Markdown 表格 / B) 列表
- 决策：A
- 理由：表格结构化、可被脚本解析、可扩展列

### ADR-002 Change 状态文件位置
- 背景：每个 change 的详细状态存放在哪里
- 选项：A) `.specs/<id>/STATE.md` / B) `.specs/STATE-<id>.md`
- 决策：A
- 理由：复用现有 per-change 目录，与 CHANGE/REQUIREMENT 等工件放一起更内聚

### ADR-003 迁移策略：首次读取自动迁移
- 背景：已有旧格式 STATE.md 如何迁移
- 选项：A) 自动检测+迁移 / B) 手动命令
- 决策：A
- 理由：零用户操作，向后兼容

### ADR-004 索引更新时机：仅阶段转换
- 背景：STATE.md 索引表何时同步
- 选项：A) 每次写入 / B) 仅阶段转换+启动+归档
- 决策：B
- 理由：减少跨文件写入，降低冲突窗口

### ADR-005 多 change 选择：交互选择+单 change 自动路由
- 背景：多活跃 change 时如何让用户选择
- 选项：A) AskUserQuestion / B) 命令行参数 / C) STATE.md 记录上次活跃
- 决策：A + 单 change 自动路由
- 理由：单 change 零操作（AC-4），多 change 最直观

## 5. 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 迁移数据丢失 | 中 | 高 | 迁移后保留旧内容注释，脚本逐字段校验 |
| 索引漂移 | 低 | 中 | validate_state.py 增加一致性校验 |
| 孤儿状态文件 | 低 | 低 | 归档流程增加删除 .specs/\<id\>/STATE.md 步骤 |
| Token 开销增加 | 低 | 低 | 索引表 < 500 字节，总增量 < 200 字节 |
| 脚本兼容性 | 高 | 中 | 统一 read_change_state() 函数复用 |

## 6. 既有架构对齐

### 触碰模块
| 文件 | 改动类型 | 改动范围 |
|------|---------|---------|
| SKILL.md | 修改 | 读状态逻辑+状态更新逻辑 |
| references/artifacts/meta-artifacts.md | 修改 | STATE.md Schema 模板 |
| references/stages/0~7（8个文件） | 修改 | 阶段进度写入目标 |
| references/stages/special-flows.md | 修改 | 归档/中断/并行/废弃/回溯 |
| references/scripts/validate_state.py | 修改 | 新格式校验+一致性 |
| references/scripts/gate_check.py | 修改 | 读 STATE.md 阶段字段适配新路径，接收 --change-id 参数 |
| references/scripts/trace_collector.py | 修改 | 读 per-change STATE |
| references/scripts/evolution_signal.py | 修改 | 读 per-change STATE |
| references/sync-workflow.md | 修改 | 状态读取路径 |
| .codex/instructions.md | 修改 | STATE.md 字段描述 |
| README.md | 修改 | 状态架构描述 |

### 禁动清单
- PIPELINE.md 结构和格式
- 归档目录结构
- CHANGE/REQUIREMENT/DESIGN/TASK 等工件模板
- 交叉评审矩阵
- 路径模式定义
- 闸门检查严格程度

### 沿用决策
- STATE.md 是唯一状态源（重新定义为索引+详情）
- 全 Markdown 格式
- 6 维交叉评审
- 闸门检查逻辑不变
- 复杂度分级不影响
