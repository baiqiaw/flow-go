# TASK — token-optimize-p0-p2

## 并行分组

- **组 A（AFK 并行）**：T01 + T05
- **组 B（串行）**：T02 → T03 → T04
- **组 C（AFK 并行）**：T06 + T07 + T08
- **组 D（验证串行）**：T09 → T10

## 依赖图

```
T01 [P] ─────────────────────────┐
T05 [P] ─────────────┐           │
                      ▼           │
T02 ──────► T03 ────► T04        │
                 │               │
                 ▼               ▼
          T06 [P] + T07 [P] + T08 [P]
                 │               │
                 └───────┬───────┘
                         ▼
                        T09
                         │
                         ▼
                        T10
```

## T01: 扩展 terse-mode.md 为 4 级分层模式
- mode: afk
- write_files: references/terse-mode.md
- verify: grep -c "tight|caveman|ultra" references/terse-mode.md ≥ 5

## T02: SKILL.md 增加 output_mode 配置 + 平台检测
- mode: colab
- write_files: SKILL.md, references/configuration.md
- verify: output_mode + CLAUDE_CONFIG_DIR + flowgo-mode 三个关键词在 SKILL.md 中命中

## T03: 实现 SessionStart Hook
- mode: afk
- write_files: hooks/flow-go-activate.js, hooks/flow-go-config.js
- verify: node -e "require('./hooks/flow-go-activate.js')" exit 0

## T04: 实现 UserPromptSubmit Hook
- mode: afk
- write_files: hooks/flow-go-mode-tracker.js
- verify: echo '{"prompt":"test"}' | node hooks/flow-go-mode-tracker.js exit 0

## T05: 实现旗标管理共享模块
- mode: afk
- write_files: hooks/flow-go-config.js
- verify: getDefaultMode() = "normal", VALID_MODES = ["normal","tight","caveman","ultra"]

## T06: 阶段文件嵌入 Auto-Clarity + 默认模式标注
- mode: colab
- write_files: references/stages/5-review.md, references/stages/6-deploy.md（+ 0-4 阶段文件标注）
- verify: grep -l "AUTO-CLARITY" references/stages/5-review.md references/stages/6-deploy.md | wc -l = 2

## T07: cross-review-matrix.md 增加子代理压缩输出契约
- mode: afk
- write_files: references/cross-review-matrix.md
- verify: 压缩输出契约 + ≤15字 双关键词命中

## T08: trace_collector.py 扩展 token 追踪
- mode: afk
- write_files: references/scripts/trace_collector.py
- verify: --help 输出含 estimate-tokens + record-tokens + stage-summary

## T09: 回归测试
- mode: hitl
- write_files: 无（如发现回归则修改源文件）
- verify: 27/27 pytest 通过

## T10: Codex CLI 兼容性验证
- mode: hitl
- write_files: 无（如发现问题则修改 SKILL.md）
- verify: 手动验证（HITL）
