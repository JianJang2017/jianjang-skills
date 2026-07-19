#!/usr/bin/env node

/**
 * Image generation script for article-illustration-tools
 *
 * Backends: codex-cli, gemini (agy), qwen (DashScope HTTP API)
 *
 * Key features:
 *  - Verifies output file actually exists (not just process exit code)
 *  - Auto-locates images written to backend-specific dirs and copies to --output
 *  - Per-image timeout + retry
 *  - Optional batch mode: --batch with multiple --prompt-file/--output pairs
 *  - Concurrency cap for batch mode (--concurrency, default 3)
 *
 * Usage:
 *   generate-image.js --prompt-file p.md --output a.png [--ar 16:9] [--provider auto|codex|gemini]
 *   generate-image.js --prompt-file p.md --output a.png --allow-ai-text
 *   generate-image.js --batch tasks.json [--concurrency 3]
 *
 * batch tasks.json: [{"prompt-file":"p1.md","output":"a.png","aspect-ratio":"16:9"}, ...]
 */

import { spawn } from 'node:child_process';
import { readFile, writeFile, copyFile, stat, readdir, mkdir } from 'node:fs/promises';
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname, basename, join } from 'node:path';
import { homedir, tmpdir } from 'node:os';

// ─── Config ─────────────────────────────────────────────────────────────────

// ─── Config file ──────────────────────────────────────────────────────────────
// 配置文件采用与 wechat_mp_publish.py 相同的 KEY=VALUE 约定，存放于用户目录，
// 避免把密钥写进仓库或命令行。默认路径可用 --config 或 IMAGE_CONFIG_FILE 覆盖。
// 读取顺序（优先级从高到低）：命令行参数 > 配置文件 > 进程环境变量 > 内置默认值。
// 支持的键：
//   IMAGE_PROVIDER          默认后端（codex/gemini/qwen/auto），默认 codex
//   DASHSCOPE_API_KEY       千问 API Key（兼容 QWEN_API_KEY）
//   QWEN_MODEL / QWEN_BASE_URL / QWEN_NEGATIVE_PROMPT   千问可选项
const DEFAULT_CONFIG_FILE = join(homedir(), '.config', 'wechat-mp', 'wechat.env.profile');

const CONFIG_KEYS = new Set([
  'IMAGE_PROVIDER',
  'DASHSCOPE_API_KEY', 'QWEN_API_KEY',
  'QWEN_MODEL', 'QWEN_BASE_URL', 'QWEN_NEGATIVE_PROMPT',
]);

function stripEnvValue(value) {
  const v = value.trim();
  if (v.length >= 2 && v[0] === v[v.length - 1] && (v[0] === '"' || v[0] === "'")) {
    return v.slice(1, -1);
  }
  return v;
}

/** 读取 KEY=VALUE 配置文件；不存在时返回空对象。仅识别白名单键。 */
function loadConfigFile(path) {
  if (!path || !existsSync(path)) return {};
  const out = {};
  for (const rawLine of readFileSync(path, 'utf-8').split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const idx = line.indexOf('=');
    const key = line.slice(0, idx).trim();
    if (CONFIG_KEYS.has(key)) out[key] = stripEnvValue(line.slice(idx + 1));
  }
  return out;
}

// 解析配置文件路径：优先 IMAGE_CONFIG_FILE 环境变量，否则默认路径。
// （命令行 --config 在 parseArgs 后二次合并，见 resolveConfig）
const FILE_CONFIG = loadConfigFile(process.env.IMAGE_CONFIG_FILE || DEFAULT_CONFIG_FILE);

/** 按 文件 > 环境变量 > 默认 的顺序取值。 */
function cfgValue(fileCfg, key, fallback = undefined, ...altEnvKeys) {
  if (fileCfg[key] != null && fileCfg[key] !== '') return fileCfg[key];
  if (process.env[key] != null && process.env[key] !== '') return process.env[key];
  for (const alt of altEnvKeys) {
    if (fileCfg[alt] != null && fileCfg[alt] !== '') return fileCfg[alt];
    if (process.env[alt] != null && process.env[alt] !== '') return process.env[alt];
  }
  return fallback;
}

const DEFAULTS = {
  // 默认后端可在配置文件用 IMAGE_PROVIDER 指定，缺省 codex
  provider: cfgValue(FILE_CONFIG, 'IMAGE_PROVIDER', 'codex'),
  aspectRatio: '16:9',
  timeoutMs: 5 * 60 * 1000,   // 5 minutes per image
  retries: 1,                  // 1 retry on failure
  concurrency: 3,              // for batch mode
};

const CODEX_GENERATED_DIR = join(homedir(), '.codex', 'generated_images');

// ─── Qwen (DashScope) config ──────────────────────────────────────────────────
// Qwen 是阿里云百炼的文生图 HTTP 服务，不同于本地 CLI 后端：
// 通过 API Key 鉴权（来自配置文件或环境变量），同步接口返回图像 URL，再下载到本地。
const QWEN = {
  // 优先 DASHSCOPE_API_KEY（官方标准变量名），兼容 QWEN_API_KEY
  apiKey: cfgValue(FILE_CONFIG, 'DASHSCOPE_API_KEY', null, 'QWEN_API_KEY'),
  // 默认北京地域旧域名（无需 WorkspaceId）；可覆盖为专属域名或新加坡地域
  baseUrl: cfgValue(FILE_CONFIG, 'QWEN_BASE_URL', 'https://dashscope.aliyuncs.com'),
  model: cfgValue(FILE_CONFIG, 'QWEN_MODEL', 'qwen-image-2.0-pro'),
  // 反向提示词：抑制常见 AI 瑕疵
  negativePrompt: cfgValue(FILE_CONFIG, 'QWEN_NEGATIVE_PROMPT',
    '低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感，构图混乱，文字模糊，扭曲'),
};
const QWEN_API_PATH = '/api/v1/services/aigc/multimodal-generation/generation';

// Process-wide set of codex source images already claimed by a task in this run.
// Prevents two concurrent batch tasks from copying the same source.
const CLAIMED_CODEX_SOURCES = new Set();

// ─── Argument parsing ───────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    provider: null,   // null = 未在命令行显式指定，后续回退到配置文件/默认
    promptFile: null,
    output: null,
    aspectRatio: DEFAULTS.aspectRatio,
    timeoutMs: DEFAULTS.timeoutMs,
    retries: DEFAULTS.retries,
    concurrency: DEFAULTS.concurrency,
    batch: null,
    allowAiText: false,
    checkPrompt: false,
    config: null,
  };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    switch (a) {
      case '--provider': case '-p': cfg.provider = args[++i]; break;
      case '--prompt-file': case '--prompt': cfg.promptFile = args[++i]; break;
      case '--output': case '-o': cfg.output = args[++i]; break;
      case '--aspect-ratio': case '--ar': cfg.aspectRatio = args[++i]; break;
      case '--timeout': cfg.timeoutMs = parseInt(args[++i], 10) * 1000; break;
      case '--retries': cfg.retries = parseInt(args[++i], 10); break;
      case '--concurrency': cfg.concurrency = parseInt(args[++i], 10); break;
      case '--batch': cfg.batch = args[++i]; break;
      case '--config': cfg.config = args[++i]; break;
      case '--allow-ai-text': cfg.allowAiText = true; break;
      case '--check-prompt': cfg.checkPrompt = true; break;
      case '--help': case '-h': showHelp(); process.exit(0);
      default:
        if (!cfg.promptFile && !a.startsWith('-')) cfg.promptFile = a;
    }
  }

  // --config 指定了自定义配置文件：重新加载并覆盖 QWEN / 默认后端
  if (cfg.config) {
    const fileCfg = loadConfigFile(resolve(cfg.config));
    if (!existsSync(resolve(cfg.config))) {
      console.error(`Warning: config file not found: ${cfg.config}`);
    }
    QWEN.apiKey = cfgValue(fileCfg, 'DASHSCOPE_API_KEY', QWEN.apiKey, 'QWEN_API_KEY');
    QWEN.baseUrl = cfgValue(fileCfg, 'QWEN_BASE_URL', QWEN.baseUrl);
    QWEN.model = cfgValue(fileCfg, 'QWEN_MODEL', QWEN.model);
    QWEN.negativePrompt = cfgValue(fileCfg, 'QWEN_NEGATIVE_PROMPT', QWEN.negativePrompt);
    if (fileCfg.IMAGE_PROVIDER) DEFAULTS.provider = fileCfg.IMAGE_PROVIDER;
  }

  // 命令行未显式指定 --provider 时，回退到配置文件/默认后端
  if (!cfg.provider) cfg.provider = DEFAULTS.provider;

  if (cfg.checkPrompt && !cfg.promptFile) {
    console.error('Error: --check-prompt requires --prompt-file');
    showHelp(); process.exit(1);
  }
  if (!cfg.checkPrompt && !cfg.batch && (!cfg.promptFile || !cfg.output)) {
    console.error('Error: --prompt-file and --output are required (or use --batch)');
    showHelp(); process.exit(1);
  }
  return cfg;
}

function showHelp() {
  console.log(`
Usage:
  generate-image.js --prompt-file <p.md> --output <out.png> [options]
  generate-image.js --batch <tasks.json> [--concurrency N]

Options:
  --provider, -p <auto|codex|gemini|qwen>   Backend selection
                                       (default: 配置文件 IMAGE_PROVIDER，缺省 codex)
  --prompt-file <path>                 Prompt markdown file
  --output, -o <path>                  Output image path (verified after generation)
  --aspect-ratio, --ar <W:H>           Aspect ratio (default: 16:9)
  --timeout <seconds>                  Per-image timeout (default: 300)
  --retries <n>                        Retries on failure (default: 1)
  --concurrency <n>                    Parallel batch jobs (default: 3)
  --batch <tasks.json>                 JSON array of {prompt-file, output, aspect-ratio?}
  --config <path>                      配置文件路径
                                       (默认 ~/.config/wechat-mp/wechat.env.profile
                                        或环境变量 IMAGE_CONFIG_FILE)
  --allow-ai-text                      Allow the image model to render readable text.
                                       Off by default because names and poems may be wrong.
  --check-prompt                       Print the final prompt policy result without generating.
  --help, -h                           Show this help

Backends:
  codex   — OpenAI Codex CLI (https://openai.com/zh-Hans-CN/codex)
  gemini  — Antigravity CLI (https://antigravity.google/docs/cli-getting-started)
  qwen    — 阿里云百炼 千问文生图 HTTP API

配置文件 (KEY=VALUE，优先级：命令行 > 配置文件 > 环境变量 > 默认)：
  IMAGE_PROVIDER        默认后端 codex/gemini/qwen/auto（缺省 codex）
  DASHSCOPE_API_KEY     千问 API Key（兼容 QWEN_API_KEY）
  QWEN_MODEL            千问模型（默认 qwen-image-2.0-pro）
  QWEN_BASE_URL         接口域名（默认 https://dashscope.aliyuncs.com，可改专属/新加坡域名）
  QWEN_NEGATIVE_PROMPT  反向提示词
`);
}

// ─── Utilities ──────────────────────────────────────────────────────────────

async function exists(path) {
  try { await stat(path); return true; } catch { return false; }
}

async function fileSize(path) {
  try { return (await stat(path)).size; } catch { return 0; }
}

/** Spawn a process with timeout. Resolves with {stdout, stderr, code}. */
function execCommand(command, args, options = {}) {
  return new Promise((resolveP, rejectP) => {
    const child = spawn(command, args, {
      stdio: options.stdio || ['ignore', 'pipe', 'pipe'],
      cwd: options.cwd,
      env: options.env,
    });
    let stdout = '', stderr = '';
    let killed = false;
    const to = options.timeoutMs ? setTimeout(() => {
      killed = true;
      child.kill('SIGKILL');
    }, options.timeoutMs) : null;

    if (child.stdout) child.stdout.on('data', d => { stdout += d.toString(); });
    if (child.stderr) child.stderr.on('data', d => {
      stderr += d.toString();
      if (options.streamStderr !== false) process.stderr.write(d);
    });
    child.on('error', err => { if (to) clearTimeout(to); rejectP(err); });
    child.on('close', code => {
      if (to) clearTimeout(to);
      if (killed) {
        rejectP(new Error(`Command timed out after ${options.timeoutMs}ms: ${command}`));
      } else if (code === 0) {
        resolveP({ stdout, stderr, code });
      } else {
        rejectP(new Error(`Command failed (code ${code}): ${stderr.trim().slice(-500)}`));
      }
    });
  });
}

async function detectProviders() {
  const out = { codex: false, gemini: false, qwen: false };
  try { await execCommand('which', ['codex'], { streamStderr: false }); out.codex = true; } catch {}
  try { await execCommand('which', ['agy'], { streamStderr: false }); out.gemini = true; } catch {}
  // Qwen 是 HTTP API，"可用"取决于是否配置了 API Key，而非本地是否装了 CLI
  if (QWEN.apiKey) out.qwen = true;
  return out;
}

/** Extract the prompt body from a markdown file. Prefers a `PROMPT:` block. */
async function readPrompt(promptFile, options = {}) {
  const content = await readFile(promptFile, 'utf-8');

  let prompt;
  // Grab everything after the `PROMPT:` marker to the end of file (or the next
  // `---` fence line). Use a greedy capture so multi-paragraph prompts — e.g. a
  // cover prompt whose poem text sits several blank-line-separated blocks down —
  // are kept in full. A non-greedy match terminated by `$`/`\n##` truncates at
  // the first blank line and silently drops the rest of the prompt.
  const m = content.match(/^PROMPT:\s*\n([\s\S]+?)(?:\n---\s*$|$(?![\s\S]))/m);
  if (m) {
    prompt = m[1].trim();
  } else {
    // Fallback: strip frontmatter, return body.
    const lines = content.split('\n');
    let inFm = false, body = [];
    for (const line of lines) {
      if (line.trim() === '---') { inFm = !inFm; continue; }
      if (!inFm) body.push(line);
    }
    prompt = body.join('\n').trim();
  }

  if (options.allowAiText) {
    validatePromptCompleteness(content, prompt, promptFile);
    return prompt;
  }

  return `${prompt}\n\nHARD CONSTRAINT: Do not render any readable text, letters, Chinese ` +
    `characters, poem lines, poet names, titles, captions, signatures, seals, logos, or ` +
    `watermarks anywhere in the image. Leave clean negative space when the composition ` +
    `needs room for separately typeset metadata.`;
}

/**
 * Guard against silent prompt truncation. If the source file declares that
 * specific text must appear in the image (a `## Text in Image` / `Text to
 * display` section, or a `text_content` frontmatter field), then the extracted
 * prompt MUST still carry that text. When the declared text contains CJK
 * characters, we require the extracted prompt to also contain CJK — otherwise
 * the poem lines were dropped and the backend would render a text-less image.
 */
function validatePromptCompleteness(content, prompt, promptFile) {
  const declaresImageText =
    /(^|\n)#{1,6}\s*Text in Image/i.test(content) ||
    /Text to display/i.test(content) ||
    /(^|\n)text_content\s*:/i.test(content);
  if (!declaresImageText) return;

  const cjk = /[一-鿿]/;
  const sourceHasCjk = cjk.test(content);
  if (sourceHasCjk && !cjk.test(prompt)) {
    throw new Error(
      `Prompt for ${basename(promptFile)} declares text-in-image (poem/title) but the ` +
      `extracted prompt contains no CJK characters — it was likely truncated. ` +
      `Aborting to avoid generating an image with missing text. ` +
      `Check the PROMPT: block in ${promptFile}.`
    );
  }
}

/** Find the newest .png/.jpg/.webp under a directory, modified after `sinceMs`. */
async function findNewestImage(dir, sinceMs) {
  if (!(await exists(dir))) return null;
  let newest = null;
  async function walk(d) {
    const entries = await readdir(d, { withFileTypes: true });
    for (const e of entries) {
      const full = join(d, e.name);
      if (e.isDirectory()) { await walk(full); continue; }
      if (!/\.(png|jpe?g|webp)$/i.test(e.name)) continue;
      const s = await stat(full);
      if (s.mtimeMs < sinceMs) continue;
      if (!newest || s.mtimeMs > newest.mtimeMs) newest = { path: full, mtimeMs: s.mtimeMs, size: s.size };
    }
  }
  try { await walk(dir); } catch {}
  return newest;
}

// ─── Codex backend ──────────────────────────────────────────────────────────

/**
 * Codex CLI workflow:
 *  1. Snapshot the set of existing codex session dirs before invocation
 *  2. Ask codex exec to generate the image
 *  3. Codex writes to ~/.codex/generated_images/<new-session>/<random>.png
 *  4. Locate the *new* session dir (set difference) and pick its newest image
 *     — this is concurrency-safe: each codex exec creates a fresh session dir
 *  5. Copy to requested output path and verify
 */
async function generateWithCodex(prompt, output, aspectRatio, opts) {
  const sinceMs = Date.now() - 5000;
  const beforeSessions = new Set(await listCodexSessions());

  const fullPrompt =
    `Generate an image and save it to ${output}.\n\n` +
    `Prompt:\n${prompt}\n\n` +
    `Aspect ratio: ${aspectRatio}\n\n` +
    `Use your image generation capability. After generation, the file should be available ` +
    `under ~/.codex/generated_images/. Do not return placeholder text.`;

  await execCommand('codex', ['exec', fullPrompt], {
    streamStderr: opts.verbose,
    timeoutMs: opts.timeoutMs,
  });

  // Find the new session dir(s) created by this invocation
  const afterSessions = await listCodexSessions();
  const newSessions = afterSessions.filter(s => !beforeSessions.has(s));

  let found = null;
  if (newSessions.length > 0) {
    // Search only new session dirs — concurrency-safe
    // Collect all candidate images, sort by mtime desc, pick first unclaimed
    const candidates = [];
    for (const sessionDir of newSessions) {
      const img = await findNewestImage(sessionDir, sinceMs);
      if (img) candidates.push(img);
    }
    candidates.sort((a, b) => b.mtimeMs - a.mtimeMs);
    for (const c of candidates) {
      if (!CLAIMED_CODEX_SOURCES.has(c.path)) { found = c; break; }
    }
  } else {
    // Fallback: scan whole generated_images dir for unclaimed images
    const img = await findNewestImage(CODEX_GENERATED_DIR, sinceMs);
    if (img && !CLAIMED_CODEX_SOURCES.has(img.path)) found = img;
  }

  if (!found) {
    throw new Error(`Codex returned but no unclaimed image found under ${CODEX_GENERATED_DIR}`);
  }
  CLAIMED_CODEX_SOURCES.add(found.path);
  if (found.size < 1024) {
    throw new Error(`Codex produced an image but it is suspiciously small (${found.size} bytes): ${found.path}`);
  }

  await mkdir(dirname(resolve(output)), { recursive: true });
  await copyFile(found.path, output);
  const destSize = await fileSize(output);
  if (destSize === 0) throw new Error(`Copy succeeded but ${output} is empty`);

  return { provider: 'codex', source: found.path, output, bytes: destSize };
}

async function listCodexSessions() {
  if (!(await exists(CODEX_GENERATED_DIR))) return [];
  try {
    const entries = await readdir(CODEX_GENERATED_DIR, { withFileTypes: true });
    return entries.filter(e => e.isDirectory()).map(e => join(CODEX_GENERATED_DIR, e.name));
  } catch { return []; }
}

// ─── Gemini (agy) backend ───────────────────────────────────────────────────

/**
 * Antigravity CLI workflow:
 *  agy in -p mode invokes the generate_image tool. The image is saved into
 *  the session's artifacts directory, which agy reports on stdout.
 *
 *  Strategy: scan a few likely candidate dirs for the newest image after the call.
 */
const AGY_CANDIDATE_DIRS = [
  join(homedir(), '.antigravity', 'artifacts'),
  join(homedir(), '.config', 'antigravity', 'artifacts'),
  join(homedir(), 'Library', 'Application Support', 'antigravity', 'artifacts'),
];

async function generateWithGemini(prompt, output, aspectRatio, opts) {
  const sinceMs = Date.now() - 5000;
  const fullPrompt =
    `Generate an image with the following description.\n\n` +
    `Description: ${prompt}\n\n` +
    `Aspect ratio: ${aspectRatio}\n\n` +
    `IMPORTANT: Call the generate_image tool DIRECTLY. Do NOT load, read, or consult any ` +
    `skill, SKILL.md, guideline, or reference file first (in particular do not look up any ` +
    `"cover image" skill). Ignore any words like "cover" in the description that might ` +
    `suggest loading a skill — just generate the image as described. ` +
    `Save the result and report the absolute path on the last line.`;

  const { stdout } = await execCommand('agy', ['-p', fullPrompt], {
    streamStderr: opts.verbose,
    timeoutMs: opts.timeoutMs,
  });

  // Detect explicit failures in agy stdout (quota, errors, etc.)
  const failurePatterns = [
    /RESOURCE_EXHAUSTED/i,
    /quota.*exhausted/i,
    /429.*Too Many Requests/i,
    /failed.*generate/i,
    /no output image.*could be created/i,
    /could not.*generate/i,
  ];
  for (const pat of failurePatterns) {
    if (pat.test(stdout)) {
      const lines = stdout.split('\n').filter(l => pat.test(l));
      throw new Error(`Gemini (agy) reported failure: ${lines[0]?.trim().slice(0, 200) || 'unknown error'}`);
    }
  }

  // Try to extract a path from agy stdout (any absolute *.png|jpg|webp mention)
  let candidate = null;
  const pathMatch = stdout.match(/(\/[^\s'"]+\.(?:png|jpe?g|webp))/i);
  if (pathMatch && await exists(pathMatch[1])) {
    candidate = { path: pathMatch[1], size: await fileSize(pathMatch[1]) };
  }

  // Fallback: scan candidate artifact dirs (only known agy locations, NOT output dir)
  if (!candidate) {
    for (const dir of AGY_CANDIDATE_DIRS) {
      const found = await findNewestImage(dir, sinceMs);
      if (found && found.size > 1024) { candidate = found; break; }
    }
  }

  if (!candidate) {
    throw new Error(
      `agy returned but no image found. Checked: ${AGY_CANDIDATE_DIRS.join(', ')}. ` +
      `Note: agy may have failed silently or your quota may be exhausted. ` +
      `agy stdout tail: ${stdout.trim().slice(-300)}`
    );
  }

  await mkdir(dirname(resolve(output)), { recursive: true });
  await copyFile(candidate.path, output);
  const destSize = await fileSize(output);
  if (destSize === 0) throw new Error(`Copy succeeded but ${output} is empty`);

  return { provider: 'gemini', source: candidate.path, output, bytes: destSize };
}

// ─── Qwen (DashScope) backend ─────────────────────────────────────────────────

/**
 * 将宽高比映射为 qwen-image-2.0 系列推荐分辨率（总像素 512² ~ 2048²）。
 * 未命中的比例按比例计算并缩放到 ~2048 长边、8 的倍数，兜底 2048*2048。
 */
function qwenSizeForAspect(aspectRatio) {
  const table = {
    '16:9': '2688*1536',
    '9:16': '1536*2688',
    '1:1': '2048*2048',
    '4:3': '2368*1728',
    '3:4': '1728*2368',
    '2.35:1': '2048*872',
  };
  if (table[aspectRatio]) return table[aspectRatio];

  const m = String(aspectRatio || '').match(/^(\d+(?:\.\d+)?)\s*[:x×]\s*(\d+(?:\.\d+)?)$/);
  if (m) {
    const w = parseFloat(m[1]), h = parseFloat(m[2]);
    if (w > 0 && h > 0) {
      const long = 2048;
      const round8 = n => Math.max(512, Math.min(2048, Math.round(n / 8) * 8));
      const [width, height] = w >= h
        ? [long, round8(long * h / w)]
        : [round8(long * w / h), long];
      return `${round8(width)}*${round8(height)}`;
    }
  }
  return '2048*2048';
}

/**
 * Qwen 文生图工作流（同步接口）：
 *  1. POST 提示词到 DashScope multimodal-generation 接口
 *  2. 响应含临时图像 URL（24h 有效）
 *  3. 下载图像字节并写入 --output，校验非空
 */
async function generateWithQwen(prompt, output, aspectRatio, opts) {
  if (!QWEN.apiKey) {
    throw new Error('Qwen 后端需要 API Key：请设置环境变量 DASHSCOPE_API_KEY（或 QWEN_API_KEY）。');
  }
  const url = QWEN.baseUrl.replace(/\/+$/, '') + QWEN_API_PATH;
  const size = qwenSizeForAspect(aspectRatio);
  if (opts.verbose) console.log(`   qwen model=${QWEN.model} size=${size}`);

  const body = {
    model: QWEN.model,
    input: {
      messages: [{ role: 'user', content: [{ text: prompt }] }],
    },
    parameters: {
      negative_prompt: QWEN.negativePrompt,
      prompt_extend: true,
      watermark: false,
      size,
      n: 1,
    },
  };

  const controller = new AbortController();
  const to = opts.timeoutMs ? setTimeout(() => controller.abort(), opts.timeoutMs) : null;
  let data;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${QWEN.apiKey}`,
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const text = await res.text();
    try { data = JSON.parse(text); } catch { data = { raw: text }; }
    if (!res.ok) {
      const detail = data.message || data.raw || `HTTP ${res.status}`;
      throw new Error(`Qwen API 调用失败 (${res.status} ${data.code || ''}): ${String(detail).slice(0, 300)}`);
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error(`Qwen API 请求超时（${opts.timeoutMs}ms）`);
    }
    throw err;
  } finally {
    if (to) clearTimeout(to);
  }

  // 提取图像 URL：output.choices[0].message.content[].image
  const choices = data?.output?.choices;
  let imageUrl = null;
  if (Array.isArray(choices)) {
    for (const c of choices) {
      const content = c?.message?.content;
      if (Array.isArray(content)) {
        const withImage = content.find(x => x && x.image);
        if (withImage) { imageUrl = withImage.image; break; }
      }
    }
  }
  if (!imageUrl) {
    throw new Error(`Qwen 返回成功但未找到图像 URL。响应片段：${JSON.stringify(data).slice(0, 300)}`);
  }

  // 下载图像字节
  const imgRes = await fetch(imageUrl);
  if (!imgRes.ok) {
    throw new Error(`下载 Qwen 图像失败 (HTTP ${imgRes.status}): ${imageUrl.slice(0, 120)}`);
  }
  const buf = Buffer.from(await imgRes.arrayBuffer());
  if (buf.length < 1024) {
    throw new Error(`Qwen 图像字节异常小（${buf.length} bytes），疑似下载失败`);
  }

  await mkdir(dirname(resolve(output)), { recursive: true });
  await writeFile(output, buf);
  const destSize = await fileSize(output);
  if (destSize === 0) throw new Error(`写入成功但 ${output} 为空`);

  return { provider: 'qwen', source: imageUrl, output, bytes: destSize };
}

// ─── Orchestration ──────────────────────────────────────────────────────────

async function pickProvider(requested, available) {
  if (requested === 'auto') {
    if (available.codex) return 'codex';
    if (available.gemini) return 'gemini';
    if (available.qwen) return 'qwen';
    throw new Error('No image generation backend available. Install codex-cli / agy, or set DASHSCOPE_API_KEY for qwen.');
  }
  if (!available[requested]) {
    const tool = requested === 'codex' ? 'codex-cli'
      : requested === 'gemini' ? 'agy (Antigravity CLI)'
      : requested === 'qwen' ? 'qwen (设置 DASHSCOPE_API_KEY 环境变量)'
      : requested;
    throw new Error(`Provider "${requested}" is not available. Install/configure ${tool}.`);
  }
  return requested;
}

/** Run a single generation task with retries. */
async function runOne(task, providers, opts) {
  const provider = await pickProvider(task.provider || opts.provider, providers);
  const allowAiText = task.allowAiText ?? opts.allowAiText;
  const prompt = await readPrompt(task.promptFile, { allowAiText });

  let lastErr = null;
  const maxAttempts = (opts.retries ?? DEFAULTS.retries) + 1;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const tag = `[${basename(task.output)}]`;
    const attemptLabel = maxAttempts > 1 ? ` (attempt ${attempt}/${maxAttempts})` : '';
    console.log(`${tag} Generating via ${provider}${attemptLabel}...`);
    try {
      const fn = provider === 'codex' ? generateWithCodex
        : provider === 'gemini' ? generateWithGemini
        : generateWithQwen;
      const result = await fn(prompt, task.output, task.aspectRatio || opts.aspectRatio, {
        timeoutMs: opts.timeoutMs,
        verbose: opts.verbose ?? true,
      });
      console.log(`${tag} ✅ ${result.bytes} bytes → ${result.output}`);
      return { ok: true, ...result, promptFile: task.promptFile, textMode: allowAiText ? 'ai-rendered' : 'none' };
    } catch (err) {
      lastErr = err;
      console.error(`${tag} ❌ ${err.message}`);
      if (attempt < maxAttempts) console.log(`${tag} retrying...`);
    }
  }
  return { ok: false, error: lastErr?.message, promptFile: task.promptFile, output: task.output, provider };
}

/** Run multiple tasks with bounded concurrency. */
async function runBatch(tasks, providers, opts) {
  const results = new Array(tasks.length);
  let cursor = 0;
  const workers = Array.from({ length: Math.max(1, opts.concurrency) }, async () => {
    while (true) {
      const i = cursor++;
      if (i >= tasks.length) return;
      results[i] = await runOne(tasks[i], providers, opts);
    }
  });
  await Promise.all(workers);
  return results;
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const cfg = parseArgs();
  console.log('🎨 Article Illustration Tools - Image Generator');

  if (cfg.checkPrompt) {
    const prompt = await readPrompt(cfg.promptFile, { allowAiText: cfg.allowAiText });
    console.log(JSON.stringify({
      success: true,
      promptFile: cfg.promptFile,
      textMode: cfg.allowAiText ? 'ai-rendered' : 'none',
      prompt,
    }));
    return;
  }

  const providers = await detectProviders();
  const availableList = Object.keys(providers).filter(k => providers[k]).join(', ') || 'none';
  console.log(`Available backends: ${availableList}`);

  // Build task list
  let tasks;
  if (cfg.batch) {
    const raw = JSON.parse(await readFile(cfg.batch, 'utf-8'));
    if (!Array.isArray(raw)) throw new Error('--batch file must be a JSON array');
    tasks = raw.map(t => ({
      promptFile: t['prompt-file'] || t.promptFile,
      output: t.output,
      aspectRatio: t['aspect-ratio'] || t.aspectRatio,
      provider: t.provider,
      allowAiText: t['allow-ai-text'] ?? t.allowAiText ?? false,
    }));
    for (const t of tasks) {
      if (!t.promptFile || !t.output) throw new Error('Each batch task needs prompt-file and output');
    }
    console.log(`Batch mode: ${tasks.length} tasks, concurrency=${cfg.concurrency}`);
  } else {
    tasks = [{
      promptFile: cfg.promptFile,
      output: cfg.output,
      aspectRatio: cfg.aspectRatio,
      allowAiText: cfg.allowAiText,
    }];
  }

  const opts = {
    provider: cfg.provider,
    aspectRatio: cfg.aspectRatio,
    timeoutMs: cfg.timeoutMs,
    retries: cfg.retries,
    concurrency: cfg.concurrency,
    verbose: !cfg.batch, // quieter in batch mode
    allowAiText: cfg.allowAiText,
  };

  const results = tasks.length === 1
    ? [await runOne(tasks[0], providers, opts)]
    : await runBatch(tasks, providers, opts);

  // Summary
  const ok = results.filter(r => r.ok).length;
  const fail = results.length - ok;
  console.log(`\n──────────────────────────────────────────`);
  console.log(`Summary: ${ok} succeeded, ${fail} failed (out of ${results.length})`);

  // Final JSON line for programmatic consumers (always last line of stdout)
  const exitOk = fail === 0;
  console.log(JSON.stringify({ success: exitOk, count: results.length, succeeded: ok, failed: fail, results }));
  process.exit(exitOk ? 0 : 1);
}

main().catch(err => {
  console.error('❌ Fatal:', err.message);
  console.log(JSON.stringify({ success: false, error: err.message }));
  process.exit(1);
});
