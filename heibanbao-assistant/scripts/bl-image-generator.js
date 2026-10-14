#!/usr/bin/env node

/**
 * 百炼 CLI (bl) 图像生成后端
 *
 * 支持阿里云百炼平台的图像生成模型（Qwen-Image / wan2.x 系列）
 * 文档：https://bailian.aliyun.com/cli/install.md
 *
 * 功能特性：
 *  - 支持多种百炼模型（qwen-image-2.0, qwen-image-2.0-pro, wan2.6-t2i 等）
 *  - 支持自定义分辨率（宽高比或像素尺寸）
 *  - 支持 Prompt 智能改写（prompt-extend）
 *  - 支持负面提示词（negative-prompt）
 *  - 支持批量生成（--n 1-6 张）
 *  - 支持并发生成（--concurrent）
 *  - 自动从 .env 读取配置
 */

import { readFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

// ─── 配置 ───────────────────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 宽高比到尺寸的映射（推荐值，来自百炼文档）
const ASPECT_RATIO_MAP = {
  '16:9': '2688*1536',
  '9:16': '1536*2688',
  '1:1': '2048*2048',
  '4:3': '2368*1728',
  '3:4': '1728*2368',
};

// 默认配置
const DEFAULTS = {
  model: 'qwen-image-2.0-pro-2026-04-22',
  promptExtend: true,
  watermark: false,
  n: 1,
};

// ─── 环境变量加载 ───────────────────────────────────────────────────────────

async function loadEnv() {
  const config = {
    model: process.env.BL_IMAGE_MODEL || DEFAULTS.model,
    promptExtend: process.env.BL_PROMPT_EXTEND !== 'false', // default true
    watermark: process.env.BL_WATERMARK === 'true', // default false
    n: parseInt(process.env.BL_IMAGE_COUNT || String(DEFAULTS.n), 10),
    apiKey: process.env.BL_API_KEY,
    baseUrl: process.env.BL_BASE_URL,
  };

  // 尝试从项目 .env 文件加载（如果环境变量未设置）
  try {
    const envPath = resolve(__dirname, '..', '.env');
    const envContent = await readFile(envPath, 'utf-8');

    for (const line of envContent.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) continue;

      const [key, ...valueParts] = trimmed.split('=');
      const value = valueParts.join('=').replace(/^["']|["']$/g, '').trim();

      if (key === 'BL_IMAGE_MODEL' && !process.env.BL_IMAGE_MODEL) config.model = value;
      if (key === 'BL_PROMPT_EXTEND' && !process.env.BL_PROMPT_EXTEND) {
        config.promptExtend = value !== 'false';
      }
      if (key === 'BL_WATERMARK' && !process.env.BL_WATERMARK) {
        config.watermark = value === 'true';
      }
      if (key === 'BL_IMAGE_COUNT' && !process.env.BL_IMAGE_COUNT) {
        config.n = parseInt(value, 10) || DEFAULTS.n;
      }
      if (key === 'BL_API_KEY' && !config.apiKey) config.apiKey = value;
      if (key === 'BL_BASE_URL' && !config.baseUrl) config.baseUrl = value;
    }
  } catch (err) {
    // .env 文件不存在时忽略
  }

  return config;
}

// ─── bl CLI 调用封装 ────────────────────────────────────────────────────────

/**
 * 调用 bl image generate 生成图片
 * @param {string} prompt - 提示词
 * @param {object} options - 生成选项
 * @returns {Promise<{urls: string[], model: string}>}
 */
async function generateImage(prompt, options = {}) {
  const config = await loadEnv();

  // 合并配置：命令行选项 > .env > 默认值
  const model = options.model || config.model;
  const size = options.size || ASPECT_RATIO_MAP[options.aspectRatio] || ASPECT_RATIO_MAP['16:9'];
  const n = options.n || config.n;
  const promptExtend = options.promptExtend !== undefined ? options.promptExtend : config.promptExtend;
  const watermark = options.watermark !== undefined ? options.watermark : config.watermark;
  const negativePrompt = options.negativePrompt;
  const seed = options.seed;
  const concurrent = options.concurrent || 1;
  const timeout = options.timeout || 300; // 默认 5 分钟

  // 构建 bl 命令参数
  const args = [
    'image', 'generate',
    '--prompt', prompt,
    '--model', model,
    '--size', size,
    '--n', String(n),
    '--output', 'json',
  ];

  // 可选参数
  if (promptExtend !== undefined) {
    args.push('--prompt-extend', String(promptExtend));
  }
  if (watermark !== undefined) {
    args.push('--watermark', String(watermark));
  }
  if (negativePrompt) {
    args.push('--negative-prompt', negativePrompt);
  }
  if (seed !== undefined) {
    args.push('--seed', String(seed));
  }
  if (concurrent > 1) {
    args.push('--concurrent', String(concurrent));
  }
  if (config.apiKey) {
    args.push('--api-key', config.apiKey);
  }
  if (config.baseUrl) {
    args.push('--base-url', config.baseUrl);
  }

  args.push('--timeout', String(timeout));

  // 执行命令
  return new Promise((resolve, reject) => {
    let stdout = '';
    let stderr = '';

    const proc = spawn('bl', args, {
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    proc.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });

    proc.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`bl image generate failed (exit ${code}):\n${stderr}`));
        return;
      }

      try {
        // 解析 JSON 输出
        const result = JSON.parse(stdout);

        // bl 返回格式：{"urls": ["https://..."], "saved": ["/path/to/file"], "total": N}
        if (!result.urls || !Array.isArray(result.urls)) {
          reject(new Error(`Unexpected bl output format: ${stdout}`));
          return;
        }

        resolve({
          urls: result.urls,
          saved: result.saved || [],
          model: model, // bl 不返回 model，使用请求的 model
          total: result.total || result.urls.length,
        });
      } catch (err) {
        reject(new Error(`Failed to parse bl output: ${err.message}\n${stdout}`));
      }
    });

    proc.on('error', (err) => {
      reject(new Error(`Failed to spawn bl: ${err.message}`));
    });
  });
}

// ─── 导出 ───────────────────────────────────────────────────────────────────

export { loadEnv, generateImage };
