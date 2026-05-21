# CHANGE — skill-evolution-feedback

## 变更描述
flow-go 自我进化系统增加用户反馈实时捕获 + 验收分类 + SUGGEST 进化路径，解决用户口头反馈无通道、无法区分项目反馈与 skill 反馈的问题。

## 变更类型
feature

## 影响面
- 涉及架构：是（新增 SUGGEST 进化路径，与 CAPTURE/FIX/BITTER PILL 并列）
- 涉及 API：否
- 涉及数据库：否
- 需要 CONTEXT 更新：否

## 范围排除
- 不修改 evolution_signal.py 的信号检测逻辑（suggest 模式通过 skill-feedback.jsonl 直接触发，不经过信号检测）
- 不实现 skill 文件的自动修改（SUGGEST 只生成报告，全部需用户确认）
- 不增加 user_input_capture 配置项（简化实现，后续可加）

## 验收线
无（内部工具改进，不需要对外交付承诺）

## 来源
用户反馈分析 + 业界最佳实践对比（DSPy GEPA、Reflexion、Hermes 五柱架构）
