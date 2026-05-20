# SUMMARY — T01

## 做了什么
创建 trace_collector.py 轨迹采集脚本。实现 argparse CLI，接受 --specs-dir/--change-id/--health-score/--complexity/--path-mode/--tags/--output-trace/--output-jsonl 共 8 个参数。读取 STATE.md 获取阶段信息，扫描 .specs/<id>/ 下工件提取关键决策（YAML frontmatter 阶段标记、REVIEW.md 评审轮次和修复记录、各工件关键决策章节），读取 health-history.jsonl 获取最近评分，生成 TRACE.md（人类可读）和 traces.jsonl 记录（机器可读）。traces.jsonl 记录格式严格遵循 DESIGN.md 第 3.1 节定义。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/scripts/trace_collector.py | 新增 | 轨迹采集脚本，329 行 |

## Verify 输出
```
$ python3 references/scripts/trace_collector.py --help 2>&1 | grep -q "trace_collector"
$ echo $?
0
```

功能测试（临时目录 + data-flywheel 工件副本）：
```
$ python3 trace_collector.py --specs-dir ... --change-id test-change --health-score 8.5 --complexity STANDARD
轨迹已采集：test-change
  TRACE.md → .../TRACE.md
  traces.jsonl → .../traces.jsonl
```

退出码测试：
```
$ python3 trace_collector.py --specs-dir /nonexistent --change-id test 2>&1; echo $?
错误：spec 目录不存在 — /nonexistent
2

$ python3 trace_collector.py --specs-dir ... --change-id test --tags "invalid" 2>&1; echo $?
错误：--tags 参数不是合法 JSON
1
```

## 沿用既有抽象（grep 结果）
- argparse CLI 风格：health_scorer.py:10 → 沿用（argparse + description + sys.exit）
- JSONL 追加模式：health_scorer.py:236 → 沿用（open append + json.dumps）
- 退出码模式：health_scorer.py:216 → 沿用（0=成功/1=参数错误/2=工件缺失）
- 文件读取工具函数：新建（read_file 封装）

## 越界检查
- TASK write_files：1 项（references/scripts/trace_collector.py）
- 实际 diff 涉及：1 项（references/scripts/trace_collector.py）
- 越界：0

## 已知问题
- 无

## 交叉评审（独立子代理）
### 评审轮次: 2/3
### 评审矩阵
| 维度 | 结果 | 说明 |
|------|------|------|
| 规格合规 | PASS | 8 个 CLI 参数全部实现，traces.jsonl 14 个字段与 DESIGN 3.1 逐字段对齐，退出码 0/1/2 正确 |
| 设计对齐 | PASS | Python 标准库、数据流、修复项 1-6 均已落实 |
| 测试证据 | PASS | --help/退出码/功能测试全部实测通过 |
| 边界卫生 | PASS | 唯一输出文件与 TASK write_files 一致 |
| 反幻觉 | PASS | 全部 6 个 import 均为 Python 标准库 |
| 质量底线 | PASS | 无密钥/无空 catch/无逻辑 bug |

### 发现问题
- 第一轮 5 个问题（frontmatter 缺失、glob 模式、state_info 死参数、decisions type 不匹配、timestamp 时区），已全部修复

### 修复记录
| 轮次 | 问题 | 修复 | re-verify |
|------|------|------|----------|
| 1 | frontmatter 解析缺失 | 新增 parse_frontmatter_stage() | PASS |
| 1 | glob *-REVIEW.md 不匹配 REVIEW.md | 改为 *REVIEW.md | PASS |
| 1 | state_info 死参数 | TRACE.md 新增状态快照章节 | PASS |
| 1 | decisions type 值不匹配 DESIGN | STAGE_TYPE_MAP 映射 scope/architecture/task | PASS |
| 1 | timestamp UTC vs 本地时区 | datetime.now().astimezone() | PASS |
| 1 | 项目根目录计算少一级 | _project_root 上溯 2 级 | PASS |

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 2/2（首次 + 修复后） |
| 交叉评审轮次 | 2/3 |
| 代码行数变化 | +329 |
| 改动文件数 | 1 个 |
| 沿用既有抽象 | 3 个沿用 / 1 个新建 |
