# references/common/

阶段文件和特殊流程间共享的原子操作。由 stages 步骤或 special-flows.md 步骤内显式写明加载路径，按参数替换后执行。

| 文件 | 参数 | 消费方 |
|------|------|--------|
| `archive-move.md` | `{target_subpath}`：""（归档）或 "abandoned/"（废弃） | special-flows.md 归档步骤 7、废弃步骤 5 |
| `pipeline-continuation.md` | `{trigger}`：archive-complete 或 recall-start | special-flows.md 归档步骤 8.5、回溯步骤 2、SKILL.md 第一步第 8 步 |
| `debugging-protocol.md` | 无 | 3-develop.md 步骤 8、4-test.md 步骤 7 |
