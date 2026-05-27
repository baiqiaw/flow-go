#!/usr/bin/env node
// flow-go UserPromptSubmit Hook — 模式切换检测 + Per-Turn 强化
'use strict';

const fs = require('fs');

function removeFlag(path) {
  try { fs.unlinkSync(path); } catch (e) { /* silent */ }
}

function writeFlag(path, mode) {
  const config = require('./flow-go-config');
  const now = new Date().toISOString();
  config.safeWriteFlag(path, JSON.stringify({ mode, stage: null, updated: now }));
}

function handleCommand(prompt, flagPath, config) {
  const cmdMatch = prompt.match(/^\/flowgo-mode\s+(\S+)/m);
  if (!cmdMatch) return;
  const arg = cmdMatch[1].toLowerCase();
  if (arg === 'off' || arg === 'stop' || arg === 'disable') {
    removeFlag(flagPath);
  } else if (config.VALID_MODES.includes(arg)) {
    writeFlag(flagPath, arg);
  }
}

function handleNaturalLang(prompt, flagPath) {
  if (/\b(stop|disable|deactivate|turn off)\b.*\b(flowgo|flow-go)\s*mode\b/i.test(prompt) ||
      /\b(flowgo|flow-go)\s*mode\b.*\b(stop|disable|deactivate|turn off)\b/i.test(prompt)) {
    removeFlag(flagPath);
    return;
  }
  if (/\b(switch to|go back to|back to|change to|use|set)\s+normal\s*mode\b/i.test(prompt)) {
    removeFlag(flagPath);
  }
}

function handleShortcuts(promptLower, flagPath) {
  const shortcuts = {
    'caveman mode': 'caveman', 'caveman': 'caveman',
    'tight mode': 'tight', 'ultra mode': 'ultra', 'normal mode': 'normal',
  };
  for (const [keyword, mode] of Object.entries(shortcuts)) {
    if (promptLower === keyword || promptLower.startsWith(keyword + ' ')) {
      writeFlag(flagPath, mode);
      break;
    }
  }
}

function emitPerTurn(flagPath, config) {
  const flag = config.readFlag(flagPath);
  const currentMode = flag ? flag.mode : 'normal';
  const anchor = config.getStageAnchor('');
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: 'STAGE ACTIVE. 输出模式: ' + currentMode + '. ' + anchor,
    },
  }));
}

function main() {
  try {
    const config = require('./flow-go-config');
    const flagPath = config.getFlagPath();

    let input = '';
    process.stdin.setEncoding('utf-8');
    process.stdin.on('data', chunk => { input += chunk; });
    process.stdin.on('end', () => {
      try {
        const data = JSON.parse(input);
        const prompt = data.prompt || '';

        handleCommand(prompt, flagPath, config);
        handleNaturalLang(prompt, flagPath);
        handleShortcuts(prompt.toLowerCase(), flagPath);
        emitPerTurn(flagPath, config);
      } catch (e) {
        process.stdout.write('{}');
      }
    });
  } catch (e) {
    process.stdout.write('{}');
  }
}

main();
