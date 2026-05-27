#!/usr/bin/env node
// flow-go SessionStart Hook — 注入输出模式规则到会话上下文
'use strict';

const fs = require('fs');
const path = require('path');

function main() {
  try {
    const config = require('./flow-go-config');
    const mode = config.getDefaultMode();
    const flagPath = config.getFlagPath();

    const now = new Date().toISOString();
    config.safeWriteFlag(flagPath, JSON.stringify({
      mode: mode,
      stage: null,
      updated: now,
    }));

    // 输出当前模式规则到 stdout（Claude Code 注入为系统上下文）
    const tersePath = path.join(__dirname, '..', 'references', 'terse-mode.md');
    let rules = '';
    try {
      rules = fs.readFileSync(tersePath, 'utf-8');
    } catch (e) {
      rules = 'FLOW-GO OUTPUT MODE: ' + mode;
    }

    const header = 'FLOW-GO OUTPUT MODE: ' + mode + '\n\n';
    // 过滤到当前激活级别的规则
    const sections = rules.split(/\n## /);
    let output = header;
    for (const section of sections) {
      const sectionName = section.split('\n')[0].trim();
      if (sectionName.startsWith(mode) || sectionName === '保留项（全级别通用）' || sectionName === '安全自动退出') {
        output += '## ' + section + '\n';
      }
    }
    process.stdout.write(output);
  } catch (e) {
    // 静默失败，不阻塞会话启动
    process.stdout.write('FLOW-GO OUTPUT MODE: normal\n');
  }
}

main();
