#!/usr/bin/env node
// flow-go UserPromptSubmit Hook — 模式切换检测 + Per-Turn 强化
'use strict';

function main() {
  try {
    const config = require('./flow-go-config');
    const flagPath = config.getFlagPath();

    // 读取 stdin JSON
    let input = '';
    process.stdin.setEncoding('utf-8');
    process.stdin.on('data', chunk => { input += chunk; });
    process.stdin.on('end', () => {
      try {
        const data = JSON.parse(input);
        const prompt = data.prompt || '';
        const promptLower = prompt.toLowerCase();

        // 1. /flowgo-mode 命令检测
        const cmdMatch = prompt.match(/^\/flowgo-mode\s+(\S+)/m);
        if (cmdMatch) {
          const arg = cmdMatch[1].toLowerCase();
          if (arg === 'off' || arg === 'stop' || arg === 'disable') {
            try { fs.unlinkSync(flagPath); } catch (e) { /* silent */ }
          } else if (config.VALID_MODES.includes(arg)) {
            const now = new Date().toISOString();
            config.safeWriteFlag(flagPath, JSON.stringify({ mode: arg, stage: null, updated: now }));
          }
        }

        // 2. Natural language deactivation
        const fs = require('fs');
        if (/\b(stop|disable|deactivate|turn off)\b.*\b(flowgo|flow-go)\s*mode\b/i.test(prompt) ||
            /\b(flowgo|flow-go)\s*mode\b.*\b(stop|disable|deactivate|turn off)\b/i.test(prompt)) {
          try { fs.unlinkSync(flagPath); } catch (e) { /* silent */ }
        }

        // 2b. Intent-based return to normal mode
        if (/\b(switch to|go back to|back to|change to|use|set)\s+normal\s*mode\b/i.test(prompt)) {
          try { fs.unlinkSync(flagPath); } catch (e) { /* silent */ }
        }

        // 3. Direct mode keywords
        const shortcuts = {
          'caveman mode': 'caveman',
          'caveman': 'caveman',
          'tight mode': 'tight',
          'ultra mode': 'ultra',
          'normal mode': 'normal',
        };
        for (const [keyword, mode] of Object.entries(shortcuts)) {
          if (promptLower === keyword || promptLower.startsWith(keyword + ' ')) {
            const now = new Date().toISOString();
            config.safeWriteFlag(flagPath, JSON.stringify({ mode, stage: null, updated: now }));
            break;
          }
        }

        // 4. Per-Turn 强化（hookSpecificOutput）
        const flag = config.readFlag(flagPath);
        const currentMode = flag ? flag.mode : 'normal';
        const anchor = config.getStageAnchor('');
        const hookOutput = {
          hookSpecificOutput: {
            hookEventName: 'UserPromptSubmit',
            additionalContext: 'STAGE ACTIVE. 输出模式: ' + currentMode + '. ' + anchor,
          },
        };
        process.stdout.write(JSON.stringify(hookOutput));
      } catch (e) {
        // 静默失败，不阻塞用户输入
        process.stdout.write('{}');
      }
    });
  } catch (e) {
    process.stdout.write('{}');
  }
}

main();
