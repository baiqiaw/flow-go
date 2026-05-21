#!/usr/bin/env python3
"""闸门共享常量 — 危险模式 + 阈值

被 gate_l1 / gate_l2 / gate_check 等模块按需导入。
"""
import re

# 危险模式（安全扫描用）
DANGEROUS_PATTERNS = [
    r"BEGIN\s+PRIVATE\s+KEY",
    r"BEGIN\s+RSA\s+PRIVATE\s+KEY",
    r"rm\s+-rf\s+/",
    r"DROP\s+TABLE",
    r"password\s*=\s*['\"]",
]

# 效率维度阈值：AC 通过数 / (代码行数/100) 的最低比值
EFFICIENCY_THRESHOLD = 0.5
