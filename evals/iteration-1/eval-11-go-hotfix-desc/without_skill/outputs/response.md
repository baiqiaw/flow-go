我理解你遇到了生产环境内存泄漏的紧急问题，需要热修。让我帮你定位和修复。

首先，我需要了解更多信息才能有效排查：

1. **哪个服务/应用出现 OOM？** - 这个仓库是 flow-go 流程编排工具本身，还是你有其他的生产服务？
2. **OOM 的具体表现是什么？** - 是 Go runtime 的 OOM kill，还是容器/系统层面的 OOM killer？
3. **有没有 pprof 内存 profile？** - 这是定位 Go 内存泄漏最直接的方式。
4. **最近是否有部署变更？** - OOM 是什么时候开始出现的？

**紧急止血建议（在排查根因期间）：**

如果是容器部署，可以临时调整：
```yaml
resources:
  limits:
    memory: "2Gi"  # 临时提高内存限制
```

或者增加 GC 频率：
```go
// 在 main.go 启动时
debug.SetGCPercent(50) // 默认 100，调低会触发更频繁的 GC
debug.SetMemoryLimit(1 << 30) // 设置 soft memory limit
```

**排查方向：**

常见的 Go 内存泄漏模式：
- goroutine 泄漏（未正确关闭 channel / 缺少 context cancel）
- 全局 map/slice 无限增长
- time.Ticker 未 Stop
- HTTP 连接未关闭 response body
- 字符串/byte slice 的意外引用导致大对象无法 GC

如果你能提供具体的代码路径、服务名或错误日志，我可以直接帮你定位到泄漏点并写出修复代码。
