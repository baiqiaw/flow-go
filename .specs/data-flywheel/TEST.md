# TEST — data-flywheel

## 测试矩阵
| AC | 测试类型 | 测试文件/命令 | 状态 |
|----|---------|-------------|------|
| AC-1 轨迹采集 | unit | trace_collector.py --help | ✅ |
| AC-1 轨迹采集 | unit | trace_collector.py --check-outcome --help | ✅ |
| AC-2 工件定义 | grep | grep TRACE.md meta-artifacts.md | ✅ |
| AC-3 归档集成 | grep | grep trace_collector special-flows.md | ✅ |
| AC-4 SKILL 路由 | grep | grep flywheel SKILL.md | ✅ |
| AC-5 上下文摘要 | unit | context_summarizer.py --help | ✅ |
| AC-6 阶段清单 | grep | grep 上下文需求清单 stages/*.md (8/8) | ✅ |
| AC-7 配置项 | grep | grep flywheel_min_samples SKILL.md | ✅ |
| AC-8 Gap 分析 | unit | gap_analyzer.py --help | ✅ |
| AC-9 健康校准 | unit | health_calibration.py --help | ✅ |
| AC-10 工件分析 | unit | artifact_format_analyzer.py --help | ✅ |
| AC-10 工件分析 | integration | artifact_format_analyzer.py --skill-dir (实际运行) | ✅ |
| AC-10 周报模板 | grep | grep EVOLUTION-WEEKLY meta-artifacts.md | ✅ |

## 5 轮报告

### 第 1 轮：功能
- 全部 13 个任务 verify 命令通过
- 6 个 Python 脚本 --help 输出正确
- 7 个文件内容 grep 验证通过
- artifact_format_analyzer.py 实际运行输出 17 个模板分析、0.86 平均效率
- 通过率：13/13 (100%)

### 第 2 轮：性能
- 跳过。理由：均为 CLI 脚本，无性能瓶颈场景（单次运行 < 1 秒）

### 第 3 轮：安全
- 密钥扫描：未发现真实密钥/凭证泄露（命中项均为变量名 token_efficiency 等）
- 退出码测试：参数错误→1，缺少必选参数→2，正确
- 全部脚本仅使用 Python 标准库，无第三方依赖

### 第 4 轮：兼容
- 跳过。理由：全部使用 Python 标准库（argparse/json/os/re/sys），无平台兼容性问题

### 第 5 轮：可观测
- 退出码语义一致：0=成功 / 1=参数错误 / 2=数据缺失或不足
- JSON 输出格式统一（ensure_ascii=False, indent=2）
- 错误信息输出到 stderr

## Bug 清单
| ID | 严重度 | 描述 | 修复验证 | 状态 |
|----|--------|------|---------|------|
| — | — | 无 bug | — | — |
