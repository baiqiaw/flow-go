# 工件示例 — TASK.md

> 示例：对应 user-login 的 TASK.md，展示好工件的标准。

---

```markdown
# TASK — user-login

## 依赖图
T01(路由+验证) → T02(会话管理)，T01 和 T03(锁定逻辑) 并行

## 任务列表

<task id="T01" parallel="false" priority="must" type="feature">
  <name>登录路由与参数验证</name>
  <read_files>src/routes/auth.ts, src/middleware/validate.ts</read_files>
  <write_files>src/routes/login.ts, src/validators/login.ts</write_files>
  <action>创建 POST /login 路由，接收 email+password，调用 validate 校验格式，返回 400/继续</action>
  <verify>npm test -- src/routes/login.test.ts</verify>
  <done>参数验证测试全通过，非法输入返回 400</done>
  <depends_on></depends_on>
</task>

<task id="T02" parallel="false" priority="must" type="feature">
  <name>会话管理（登录成功/过期）</name>
  <read_files>src/routes/login.ts, src/lib/session.ts</read_files>
  <write_files>src/lib/session.ts, src/middleware/auth-guard.ts</write_files>
  <action>实现 session 创建/验证/过期逻辑，集成到登录路由成功分支和 auth-guard</action>
  <verify>npm test -- src/lib/session.test.ts src/middleware/auth-guard.test.ts</verify>
  <done>AC-1（正常登录）+ AC-4（会话过期）测试通过</done>
  <depends_on>T01</depends_on>
</task>

<task id="T03" parallel="true" priority="should" type="feature">
  <name>账号锁定逻辑</name>
  <read_files>src/routes/login.ts, src/lib/rate-limit.ts</read_files>
  <write_files>src/lib/login-limiter.ts</write_files>
  <action>实现连续失败计数，5 次后锁定 30 分钟，集成到登录路由失败分支</action>
  <verify>npm test -- src/lib/login-limiter.test.ts</verify>
  <done>AC-3（账号锁定）测试通过</done>
  <depends_on>T01</depends_on>
</task>
```

---

## 好工件特征

- [x] 每个任务 ≤ 1 context（< 100 行代码）
- [x] verify 是可执行命令（非"测试通过"）
- [x] 依赖关系清晰（T02→T01，T03→T01，T02‖T03）
- [x] 依赖无环
- [x] 有并行标记（T03 parallel=true）
- [x] 每个任务有 type 和 priority（任务 ≤ 3 个，跳过优先级排序）
- [x] done 条件引用 AC 编号
