#!/usr/bin/env node

/**
 * Optimize a text-to-image prompt.
 *
 * 输入：一段原始 prompt（来自用户、来自 reverse-prompt.js，或来自 prompts/ 归档）
 * 输出：按 [Style] + [Type] + [Content] + [Key elements] 结构改写后的 prompt，
 *       可选附加风格预设 (--style)。
 *
 * 后端：codex / agy。仅做"改写"，不调用生图。
 *
 * 用法 (Usage):
 *   optimize-prompt.js --prompt "<原始 prompt>"
 *   optimize-prompt.js --prompt-file prompts/20260628-01.md --style blueprint
 *   optimize-prompt.js --prompt-file p.md --style keep --archive
 *   echo "原始 prompt" | optimize-prompt.js --stdin --style hand-drawn
 *
 * Style 预设（与现有 SKILL.md 的风格关键词表对齐）：
 *   hand-drawn  → 手绘风格、warm cream 背景、黑线 + pastel 色块
 *   blueprint   → 科技蓝图、grid 背景、白色线稿
 *   watercolor  → 水彩、柔光、纸纹
 *   cyberpunk   → 赛博朋克、霓虹、雨夜街景
 *   3d          → 3D 渲染、柔光、景深
 *   healing     → 治愈系、柔色、低饱和
 *   minimal     → 极简、留白、大字
 *   photo       → 摄影风、自然光、真实质感
 *   keep        → 保留原风格，仅做结构化
 *   auto        → 让后端按原 prompt 自动判断（默认）
 */

import { spawn } from 'node:child_process';
import { readFile, writeFile, stat, mkdir, readdir } from 'node:fs/promises';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { STYLE_PRESETS } from './styles.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROMPTS_DIR = resolve(__dirname, '..', 'prompts');

const DEFAULTS = {
  provider: 'auto',
  style: 'auto',
  lang: 'zh',
  timeoutMs: 3 * 60 * 1000,
  retries: 1,
};

// 风格预设统一来自 ./styles.js（reverse / optimize / generate-portrait 共用）。
// 加新风格只改 styles.js，三个脚本自动同步。

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    prompt: null,
    promptFile: null,
    stdin: false,
    output: null,
    provider: DEFAULTS.provider,
    style: DEFAULTS.style,
    lang: DEFAULTS.lang,
    archive: false,
    aspectRatio: null,
    timeoutMs: DEFAULTS.timeoutMs,
    retries: DEFAULTS.retries,
    verbose: false,
    dryRun: false,
    json: false,
    listStyles: false,
  };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    switch (a) {
      case '--prompt': cfg.prompt = args[++i]; break;
      case '--prompt-file': case '-f': cfg.promptFile = args[++i]; break;
      case '--stdin': cfg.stdin = true; break;
      case '--output': case '-o': cfg.output = args[++i]; break;
      case '--provider': case '-p': cfg.provider = args[++i]; break;
      case '--style': case '-s': cfg.style = args[++i]; break;
      case '--lang': case '-l': cfg.lang = args[++i]; break;
      case '--archive': cfg.archive = true; break;
      case '--aspect-ratio': case '--ar': cfg.aspectRatio = args[++i]; break;
      case '--timeout': cfg.timeoutMs = parseInt(args[++i], 10) * 1000; break;
      case '--retries': cfg.retries = parseInt(args[++i], 10); break;
      case '--verbose': case '-v': cfg.verbose = true; break;
      case '--dry-run': cfg.dryRun = true; break;
      case '--json': cfg.json = true; break;
      case '--list-styles': cfg.listStyles = true; break;
      case '--help': case '-h': showHelp(); process.exit(0);
      default:
        // 位置参数：第一个非选项当 prompt
        if (cfg.prompt == null && !cfg.promptFile && !cfg.stdin && !a.startsWith('-')) cfg.prompt = a;
    }
  }
  if (cfg.listStyles) { listStyles(); process.exit(0); }
  const sources = [cfg.prompt, cfg.promptFile, cfg.stdin].filter(Boolean).length;
  if (sources === 0) {
    console.error('Error: 需要提供 --prompt / --prompt-file / --stdin 中的一种');
    showHelp(); process.exit(1);
  }
  if (sources > 1) {
    console.error('Error: --prompt / --prompt-file / --stdin 只能用一种');
    process.exit(1);
  }
  if (!STYLE_PRESETS[cfg.style]) {
    console.error(`Error: 未知风格 "${cfg.style}"。可用：${Object.keys(STYLE_PRESETS).join(', ')}`);
    process.exit(1);
  }
  return cfg;
}

function showHelp() {
  console.log(`
Optimize-prompt — 按 [Style]+[Type]+[Content]+[Key elements] 结构优化生图 prompt

Usage:
  optimize-prompt.js --prompt "原始 prompt" [--style auto] [options]
  optimize-prompt.js --prompt-file <md> [--style blueprint] [--archive]
  echo "原始 prompt" | optimize-prompt.js --stdin -s hand-drawn

Inputs (三选一):
  --prompt "<text>"            字面 prompt
  --prompt-file <md>, -f       归档过的 prompts/YYYYMMDD-NN.md 等
  --stdin                      从 stdin 读取原始 prompt

Options:
  --style, -s <preset>         风格预设 (default: auto)。--list-styles 查看全部
  --lang, -l <zh|en|auto>      输出语言 (default: zh)
  --provider, -p <auto|codex|agy>  后端
  --output, -o <path>          优化后的 prompt 写入文件 (带 frontmatter)
  --archive                    自动归档到 prompts/YYYYMMDD-NN.md
  --aspect-ratio, --ar <W:H>   frontmatter 中的 aspect_ratio
  --timeout <seconds>          后端超时 (default: 180)
  --retries <n>                重试次数 (default: 1)
  --verbose, -v                透传后端 stderr
  --dry-run                    打印将要调用的命令，不实际跑
  --json                       仅输出 JSON 结果到 stdout
  --list-styles                列出所有风格预设
  --help, -h                   显示本帮助

输出：stdout 默认输出优化后的 prompt 主体（一行一行裸文本），便于 pipe 给
generate-image.js / send_feishu_image.py / publish_*.js。
`);
}

function listStyles() {
  console.log('可用风格预设：\n');
  for (const [k, v] of Object.entries(STYLE_PRESETS)) {
    const tag = v.kind === 'portrait' ? '[人物]' : '      ';
    console.log(`  ${tag} ${k.padEnd(16)}${v.label ? v.label + '  —  ' : ''}${v.zh}`);
  }
}

// ─── Utils ──────────────────────────────────────────────────────────────────

async function exists(p) { try { await stat(p); return true; } catch { return false; } }

function execCommand(command, args, opts = {}) {
  return new Promise((resP, rejP) => {
    const child = spawn(command, args, {
      stdio: opts.stdio || ['ignore', 'pipe', 'pipe'],
      cwd: opts.cwd,
      env: opts.env,
    });
    let stdout = '', stderr = '';
    let killed = false;
    const to = opts.timeoutMs ? setTimeout(() => { killed = true; child.kill('SIGKILL'); }, opts.timeoutMs) : null;
    if (child.stdout) child.stdout.on('data', d => { stdout += d.toString(); });
    if (child.stderr) child.stderr.on('data', d => {
      stderr += d.toString();
      if (opts.streamStderr) process.stderr.write(d);
    });
    child.on('error', err => { if (to) clearTimeout(to); rejP(err); });
    child.on('close', code => {
      if (to) clearTimeout(to);
      if (killed) return rejP(new Error(`Command timed out after ${opts.timeoutMs}ms: ${command}`));
      if (code === 0) return resP({ stdout, stderr, code });
      rejP(new Error(`Command failed (code ${code}): ${stderr.trim().slice(-500) || stdout.trim().slice(-500)}`));
    });
  });
}

async function detectProviders() {
  const out = { codex: false, agy: false };
  try { await execCommand('which', ['codex'], {}); out.codex = true; } catch {}
  try { await execCommand('which', ['agy'], {}); out.agy = true; } catch {}
  return out;
}

async function pickProvider(requested, available) {
  if (requested === 'auto') {
    if (available.codex) return 'codex';
    if (available.agy) return 'agy';
    throw new Error('没找到可用的后端 (codex / agy)。');
  }
  if (requested === 'gemini') requested = 'agy';
  if (!available[requested]) throw new Error(`后端 "${requested}" 不可用`);
  return requested;
}

async function readStdin() {
  return new Promise((res, rej) => {
    let data = '';
    process.stdin.setEncoding('utf-8');
    process.stdin.on('data', c => { data += c; });
    process.stdin.on('end', () => res(data));
    process.stdin.on('error', rej);
  });
}

// 从 prompts/ 归档文件中抽出 PROMPT 段（与 generate-image.js 同款解析）
function extractPromptBody(content) {
  const m = content.match(/^PROMPT:\s*\n([\s\S]+?)(?=\n---|^\n##|(?![\s\S]))/m);
  if (m) return m[1].trim();
  // fallback: 剥掉 frontmatter
  const lines = content.split('\n');
  let inFm = false; const body = [];
  for (const line of lines) {
    if (line.trim() === '---') { inFm = !inFm; continue; }
    if (!inFm) body.push(line);
  }
  return body.join('\n').trim();
}

async function loadOriginalPrompt(cfg) {
  if (cfg.prompt) return cfg.prompt.trim();
  if (cfg.stdin) return (await readStdin()).trim();
  if (cfg.promptFile) {
    const raw = await readFile(cfg.promptFile, 'utf-8');
    return extractPromptBody(raw);
  }
  throw new Error('未提供 prompt 来源');
}

// ─── Optimization prompt 模板 ───────────────────────────────────────────────

function buildOptimizationPrompt(original, style, lang) {
  const preset = STYLE_PRESETS[style];
  const langInstruction = (() => {
    if (lang === 'en') return 'Output the optimized prompt in English.';
    if (lang === 'auto') return '原 prompt 主要是哪种语言就用哪种语言输出（技术词保留英文）。';
    return '用中文输出优化后的 prompt，技术词保留英文（如 React/PostgreSQL/3D/UI/blueprint/cyan/pastel）。';
  })();

  return [
    `你是一名"文生图 prompt 工程师"。请把下面这条原始 prompt 改写得更适合生图模型理解。`,
    ``,
    `原始 prompt：`,
    `"""`,
    original,
    `"""`,
    ``,
    `优化原则：`,
    `1. 严格按结构 [Style] + [Type] + [Content] + [Key elements] 组织：`,
    `   - Style：视觉风格（如 hand-drawn / blueprint / watercolor / cyberpunk / 3D / photo / minimal）`,
    `   - Type：图像类别（infographic / 流程图 / 架构图 / 插画 / 海报 / 摄影 / 渲染图 / 头像）`,
    `   - Content：主体内容（要画的是什么——保留原 prompt 的核心语义，不要凭空增删）`,
    `   - Key elements：构图 / 配色 / 材质 / 光照 / 关键标签文字 / 镜头`,
    `2. 写成 1-2 段紧凑的指令式 prompt，目标 120-260 字符（中文）或 25-60 词（英文）。`,
    `3. 不要 Markdown 列表、不要表情、不要解释、不要"以下是…"开头。`,
    `4. 若原 prompt 包含具体文字（架构图里的"React"/"PostgreSQL"等），要原样保留。`,
    `5. 配色 / 材质等表达可直接用英文（warm cream / pastel blocks / cinematic 等）。`,
    ``,
    `风格指令 (--style ${style})：${preset.zh}`,
    `推荐融入的修饰词：${preset.keywords}`,
    style === 'keep' ? `注意：保留原 prompt 的视觉风格，不要替换。` : '',
    style === 'auto' ? `注意：原 prompt 没有指定明确风格时，给一个最贴合主体的合理风格；如已有风格，不要覆盖。` : '',
    ``,
    `${langInstruction}`,
    ``,
    `严格按下面格式输出，不要有其它任何字：`,
    ``,
    `PROMPT:`,
    `<优化后的 prompt 主体>`,
    ``,
    `NOTES:`,
    `<一行 ≤50 字的中文备注：你做了哪些主要调整，例如"补充了配色和材质，限定为 blueprint 风">`,
  ].filter(Boolean).join('\n');
}

// ─── 后端调用 + 解析 ────────────────────────────────────────────────────────

async function callBackend(provider, prompt, opts) {
  if (provider === 'codex') {
    const { stdout } = await execCommand('codex', ['exec', '--skip-git-repo-check', prompt], {
      timeoutMs: opts.timeoutMs,
      streamStderr: opts.verbose,
    });
    return stdout;
  }
  const { stdout } = await execCommand('agy', ['-p', prompt], {
    timeoutMs: opts.timeoutMs,
    streamStderr: opts.verbose,
  });
  return stdout;
}

function parseBackendOutput(raw) {
  const text = raw.replace(/\r\n/g, '\n');
  let prompt = null;
  let notes = null;

  const pMatch = text.match(/PROMPT:\s*\n?([\s\S]+?)(?=\n\s*NOTES\s*:|\Z)/);
  if (pMatch) prompt = pMatch[1].trim();

  const nMatch = text.match(/NOTES:\s*([^\n]+(?:\n[^\n]+)*)/);
  if (nMatch) notes = nMatch[1].trim();

  if (!prompt) {
    const cleaned = text
      .split('\n')
      .filter(l => !/^(thinking|codex|tokens used|\[.*\])/i.test(l.trim()))
      .join('\n')
      .trim();
    if (cleaned.length > 0) prompt = cleaned.slice(0, 2000);
  }
  if (prompt) {
    prompt = prompt.split('\n').filter(l => !/^\s*NOTES\s*:/.test(l)).join('\n').trim();
  }
  return { prompt, notes };
}

// ─── 归档 ───────────────────────────────────────────────────────────────────

async function nextArchiveFilename() {
  await mkdir(PROMPTS_DIR, { recursive: true });
  const today = new Date();
  const yyyymmdd = `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`;
  let maxSeq = 0;
  try {
    const entries = await readdir(PROMPTS_DIR);
    for (const f of entries) {
      const m = f.match(/^(\d{8})-(\d{2})\.md$/);
      if (!m || m[1] !== yyyymmdd) continue;
      maxSeq = Math.max(maxSeq, parseInt(m[2], 10));
    }
  } catch {}
  return join(PROMPTS_DIR, `${yyyymmdd}-${String(maxSeq + 1).padStart(2, '0')}.md`);
}

function buildFileContent(prompt, meta) {
  const lines = ['---'];
  lines.push(`aspect_ratio: "${meta.aspectRatio || 'auto'}"`);
  lines.push(`provider: ${meta.provider}`);
  lines.push(`source: optimize`);
  lines.push(`style: ${meta.style}`);
  if (meta.notes) lines.push(`notes: ${JSON.stringify(meta.notes)}`);
  lines.push(`timestamp: ${new Date().toISOString()}`);
  lines.push('---');
  lines.push('');
  lines.push('PROMPT:');
  lines.push(prompt);
  lines.push('');
  return lines.join('\n');
}

// ─── 主流程 ─────────────────────────────────────────────────────────────────

async function main() {
  const cfg = parseArgs();

  const original = await loadOriginalPrompt(cfg);
  if (!original) {
    console.error('❌ 原始 prompt 为空');
    process.exit(1);
  }

  const providers = await detectProviders();
  const provider = await pickProvider(cfg.provider, providers);
  const fullPrompt = buildOptimizationPrompt(original, cfg.style, cfg.lang);

  if (cfg.dryRun) {
    console.error('🧪 Dry-run');
    console.error(`  Provider : ${provider}`);
    console.error(`  Style    : ${cfg.style}  (${STYLE_PRESETS[cfg.style].zh})`);
    console.error(`  Lang     : ${cfg.lang}`);
    console.error(`  Archive  : ${cfg.archive}`);
    console.error('─── 原始 prompt ───');
    console.error(original);
    console.error('─── optimization prompt 预览 ───');
    console.error(fullPrompt);
    process.exit(0);
  }

  let raw = null;
  let lastErr = null;
  const maxAttempts = cfg.retries + 1;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    if (!cfg.json) console.error(`✨ 优化中 (${provider}, style=${cfg.style}, attempt ${attempt}/${maxAttempts})...`);
    try {
      raw = await callBackend(provider, fullPrompt, cfg);
      break;
    } catch (e) {
      lastErr = e;
      if (!cfg.json) console.error(`⚠️  ${e.message}`);
    }
  }
  if (raw === null) {
    console.error(`❌ 优化失败：${lastErr?.message || 'unknown'}`);
    if (cfg.json) console.log(JSON.stringify({ success: false, error: lastErr?.message || 'unknown' }));
    process.exit(1);
  }

  const parsed = parseBackendOutput(raw);
  if (!parsed.prompt) {
    console.error('❌ 后端没有产出可解析的 PROMPT 段');
    if (cfg.verbose) console.error(raw.slice(-2000));
    process.exit(1);
  }

  let outputPath = null;
  let archivePath = null;
  const meta = { aspectRatio: cfg.aspectRatio, provider, style: cfg.style, notes: parsed.notes };
  const fileContent = buildFileContent(parsed.prompt, meta);

  if (cfg.output) {
    await mkdir(dirname(resolve(cfg.output)), { recursive: true });
    await writeFile(cfg.output, fileContent, 'utf-8');
    outputPath = resolve(cfg.output);
  }
  if (cfg.archive) {
    archivePath = await nextArchiveFilename();
    await writeFile(archivePath, fileContent, 'utf-8');
  }

  if (cfg.json) {
    console.log(JSON.stringify({
      success: true,
      provider,
      style: cfg.style,
      prompt: parsed.prompt,
      notes: parsed.notes,
      original,
      output: outputPath,
      archive: archivePath,
    }, null, 2));
  } else {
    console.error('');
    console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.error(`✅ 优化完成 · provider=${provider} · style=${cfg.style}`);
    if (parsed.notes) console.error(`📝 备注：${parsed.notes}`);
    if (outputPath) console.error(`📄 已写入：${outputPath}`);
    if (archivePath) console.error(`🗄  已归档：${archivePath}`);
    console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(parsed.prompt);
  }
  process.exit(0);
}

main().catch(err => {
  console.error('❌ Fatal:', err.message);
  process.exit(1);
});
