// flow-go 旗标管理共享模块
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const VALID_MODES = ['normal', 'tight', 'caveman', 'ultra'];

const STAGE_ANCHORS = {
  '0-需求': '不确定就问，不猜不假设',
  '1-设计': '每个决策有替代方案',
  '2-任务': '每个 task 可独立验证',
  '3-开发': '每行改动追溯到需求',
  '4-测试': '按验收标准写用例，不改实现',
  '5-审查': '所有级别问题 = 0 才过关',
  '6-部署': '部署前有回滚方案',
  '7-验收': '逐条对照 AC 验收',
};

function getFlagPath() {
  const configDir = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
  return path.join(configDir, '.flowgo-mode');
}

function getDefaultMode() {
  if (process.env.FLOWGO_DEFAULT_MODE && VALID_MODES.includes(process.env.FLOWGO_DEFAULT_MODE)) {
    return process.env.FLOWGO_DEFAULT_MODE;
  }
  return 'normal';
}

function safeWriteFlag(flagPath, content) {
  try {
    const dir = path.dirname(flagPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    // 防符号链接检查
    const realDir = fs.realpathSync(dir);
    if (realDir !== fs.realpathSync(path.resolve(dir))) {
      return false;
    }
    const tmpPath = flagPath + '.' + Date.now() + '.tmp';
    const fd = fs.openSync(tmpPath, 'w', 0o600);
    fs.writeFileSync(fd, content, 'utf-8');
    fs.closeSync(fd);
    fs.renameSync(tmpPath, flagPath);
    return true;
  } catch (e) {
    return false;
  }
}

function readFlag(flagPath) {
  try {
    const realPath = fs.realpathSync(flagPath);
    if (realPath !== path.resolve(flagPath)) {
      return null;
    }
    const stat = fs.statSync(flagPath);
    if (stat.size > 4096) {
      return null;
    }
    const content = fs.readFileSync(flagPath, 'utf-8');
    const data = JSON.parse(content);
    if (!data.mode || !VALID_MODES.includes(data.mode)) {
      return null;
    }
    return data;
  } catch (e) {
    return null;
  }
}

function getStageAnchor(stage) {
  return STAGE_ANCHORS[stage] || '';
}

module.exports = {
  VALID_MODES,
  STAGE_ANCHORS,
  getFlagPath,
  getDefaultMode,
  safeWriteFlag,
  readFlag,
  getStageAnchor,
};
