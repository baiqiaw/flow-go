# SUMMARY — T08

## 做了什么
扩展 references/scripts/trace_collector.py，增加 token 追踪功能：--estimate-tokens 启发式估算（len/4）、--record-tokens 记录到 traces.jsonl、--stage-summary per-stage 汇总。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/scripts/trace_collector.py | 修改 | +92/-2，新增 token 追踪功能和 3 个 CLI 选项 |

## Verify 输出
```
$ python references/scripts/trace_collector.py --help | grep -E "estimate-tokens|record-tokens|stage-summary"
  --estimate-tokens   使用 len(text)/4 启发式估算 token 数（默认关闭）
  --record-tokens     记录 token 数据到 traces.jsonl（默认关闭）
  --stage-summary     输出 per-stage token 汇总（默认关闭）
```

## 沿用既有抽象（grep 结果）
- 沿用 trace_collector.py 已有的 argparse CLI 框架
- 沿用 traces.jsonl 追加写入模式
- tokens 字段可选，向后兼容旧记录

## 越界检查
- TASK write_files：1 项
- 实际 diff 涉及：1 项
- 越界：0

## 已知问题
首轮 --specs-dir=None 导致 TypeError，已修复：在 main() 中增加 `args.specs_dir is None` 前置检查，输出错误消息后 sys.exit(2)。

## 交叉评审（独立子代理）
### 评审矩阵
| 维度 | 结果 | 说明 |
|------|------|------|
| 规格合规 | PASS | --help 三选项可见（estimate-tokens/record-tokens/stage-summary） |
| 设计对齐 | PASS | len/4 启发式与 ADR-004 一致 |
| 测试证据 | PASS | --help 输出真实命令结果 |
| 边界卫生 | PASS | 仅改动 trace_collector.py |
| 反幻觉 | PASS | 无外部依赖，仅使用 Python 标准库 |
| 质量底线 | PASS | --specs-dir None 前置检查已修复 |

### 发现问题
| 问题 | 严重度 | 修复 |
|------|--------|------|
| --specs-dir=None 导致 TypeError（argparse 传递默认值 None） | Critical (91%) | main() 中增加 `args.specs_dir is None` 前置检查 |

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 1/1（首次修复后） |
| 代码行数变化 | +92/-2 |
| 改动文件数 | 1 个 |
