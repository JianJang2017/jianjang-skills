#!/usr/bin/env node

/**
 * generate-portrait-prompt.js — 按"用户主体描述 + 风格预设"生成人物图 prompt
 *
 * 与 reverse / optimize 并列的第三个 prompt 工具：
 *   - reverse  : 图  → prompt
 *   - optimize : prompt → 更好的 prompt
 *   - portrait : 一句话主体 + 风格 → 一条"开箱即生图"的人物图 prompt（本脚本）
 *
 * 输入：--subject "一句话主体"（如"一位回眸的少女""读书的白发老者"）
 *       --style  <预设>（默认 gufeng-portrait；--list-styles 看全部）
 * 输出：按 [Style] + [Type] + [Content] + [Key elements] + 镜头/光照/画质 + 负面提示
 *       组织的人物图 prompt，格式与 prompts/ 归档一致，可直接喂 generate-image.js。
 *
 * 后端：codex / agy（与生图、reverse、optimize 共用，无新依赖）。
 *
 * 用法 (Usage):
 *   generate-portrait-prompt.js --subject "一位临窗抚琴的古风少女"
 *   generate-portrait-prompt.js -S "雪中红衣女子回眸" -s gufeng-portrait --archive --ar 3:4
 *   generate-portrait-prompt.js -S "咖啡馆里看书的女孩" -s photo-portrait -o p.md
 *   generate-portrait-prompt.js --list-styles
 */

import { spawn } from 'node:child_process';
import { writeFile, stat, mkdir, readdir } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { STYLE_PRESETS, getStyle } from './styles.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROMPTS_DIR = resolve(__dirname, '..', 'prompts');

const DEFAULTS = {
  provider: 'auto',
  style: 'gufeng-portrait',   // 本脚本主打古风写真，默认就给它
  lang: 'zh',
  aspectRatio: '3:4',         // 人物竖图最常用
  timeoutMs: 3 * 60 * 1000,
  retries: 1,
};

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    subject: null,
    style: DEFAULTS.style,
    output: null,
    provider: DEFAULTS.provider,
    lang: DEFAULTS.lang,
    aspectRatio: DEFAULTS.aspectRatio,
    archive: false,
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
      case '--subject': case '-S': cfg.subject = args[++i]; break;
      case '--style': case '-s': cfg.style = args[++i]; break;
      case '--output': case '-o': cfg.output = args[++i]; break;
      case '--provider': case '-p': cfg.provider = args[++i]; break;
      case '--lang': case '-l': cfg.lang = args[++i]; break;
      case '--aspect-ratio': case '--ar': cfg.aspectRatio = args[++i]; break;
      case '--archive': cfg.archive = true; break;
      case '--timeout': cfg.timeoutMs = parseInt(args[++i], 10) * 1000; break;
      case '--retries': cfg.retries = parseInt(args[++i], 10); break;
      case '--verbose': case '-v': cfg.verbose = true; break;
      case '--dry-run': cfg.dryRun = true; break;
      case '--json': cfg.json = true; break;
      case '--list-styles': cfg.listStyles = true; break;
      case '--help': case '-h': showHelp(); process.exit(0);
      default:
        if (cfg.subject == null && !a.startsWith('-')) cfg.subject = a;
    }
  }
  if (cfg.listStyles) { printStyles(); process.exit(0); }
  if (!cfg.subject) {
    console.error('Error: 需要 --subject "一句话主体描述"');
    showHelp(); process.exit(1);
  }
  if (!getStyle(cfg.style)) {
    console.error(`Error: 未知风格 "${cfg.style}"。用 --list-styles 查看可用风格。`);
    process.exit(1);
  }
  return cfg;
}

function printStyles() {
  console.log('可用风格预设（[人物] 为人物写真专用，推荐用于本脚本）：\n');
  for (const [k, v] of Object.entries(STYLE_PRESETS)) {
    if (k === 'keep' || k === 'auto') continue;
    const tag = v.kind === 'portrait' ? '[人物]' : '[通用]';
    console.log(`  ${tag} ${k.padEnd(16)}${v.label ? v.label + '  —  ' : ''}${v.zh}`);
  }
  console.log('\n提示：扩展风格只需编辑 scripts/styles.js，加一条 kind:"portrait" 的预设即可。');
}

function showHelp() {
  console.log(`
generate-portrait-prompt — 主体描述 + 风格 → 人物图生图 prompt

Usage:
  generate-portrait-prompt.js --subject "一句话主体" [--style gufeng-portrait] [options]

Options:
  --subject, -S <text>         人物主体描述（必填），如"临窗抚琴的古风少女"
  --style, -s <preset>         风格预设 (default: gufeng-portrait)。--list-styles 看全部
  --aspect-ratio, --ar <W:H>   长宽比 (default: 3:4 竖图)
  --lang, -l <zh|en|auto>      输出语言 (default: zh)
  --provider, -p <auto|codex|agy>  后端
  --output, -o <path>          prompt 写入文件（带 frontmatter）
  --archive                    自动归档到 prompts/YYYYMMDD-NN.md (source: portrait)
  --timeout <seconds>          后端超时 (default: 180)
  --retries <n>                重试次数 (default: 1)
  --verbose, -v                透传后端 stderr
  --dry-run                    打印将要调用的 prompt，不实际跑后端
  --json                       仅输出 JSON 结果
  --list-styles                列出风格预设
  --help, -h                   显示本帮助

输出：一条"开箱即生图"的人物图 prompt（含风格 / 镜头 / 光照 / 画质 / 负面提示），
stdout 裸 prompt 可直接 pipe 给 generate-image.js：

Examples:
  generate-portrait-prompt.js -S "雪中红衣女子回眸" -s gufeng-portrait --archive
  generate-portrait-prompt.js -S "咖啡馆看书的女孩" -s photo-portrait -o p.md
  generate-portrait-prompt.js -S "临窗抚琴的古风少女" \\
    | node scripts/generate-image.js --stdin --output portrait.png --ar 3:4
`);
}

// ─── Utils ──────────────────────────────────────────────────────────────────

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

function pickProvider(requested, available) {
  if (requested === 'auto') {
    if (available.codex) return 'codex';
    if (available.agy) return 'agy';
    throw new Error('没找到可用的后端 (codex / agy)。请先安装其中之一。');
  }
  if (requested === 'gemini') requested = 'agy';
  if (!available[requested]) throw new Error(`后端 "${requested}" 不可用。已安装的：${Object.keys(available).filter(k => available[k]).join(', ') || '(无)'}`);
  return requested;
}

// ─── Prompt 模板 ────────────────────────────────────────────────────────────

function buildGenerationPrompt(subject, style, lang) {
  const preset = getStyle(style);
  const p = preset.portrait || {};
  const langInstruction = (() => {
    if (lang === 'en') return 'Output the final image prompt in English.';
    if (lang === 'auto') return '主体若是中式题材用中文（技术词保留英文），西式题材可用英文。';
    return '用中文输出最终 prompt，技术词 / 画质词（如 85mm / photorealistic / best quality）保留英文。';
  })();

  const portraitGuidance = preset.portrait
    ? [
        ``,
        `该风格的人物图拍摄指引（请融入对应段落）：`,
        `- 镜头 (camera)：${p.camera || '半身特写，浅景深'}`,
        `- 光照 (lighting)：${p.lighting || '柔和自然光'}`,
        `- 构图/背景 (composition)：${p.composition || '三分构图，背景虚化'}`,
        `- 画质 (quality)：${p.quality || '高细节、photorealistic、best quality'}`,
        `- 负面提示 (negative)：${p.negative || '避免：水印、变形手部、低分辨率'}`,
      ].join('\n')
    : `\n（该风格未提供专门的人物拍摄指引，按通用人像处理：半身特写、浅景深、柔光、高细节。）`;

  return [
    `你是一名"文生图 prompt 工程师"，擅长写人物图（portrait）的生图 prompt。`,
    `请基于下面的"主体描述 + 风格"，写出一条开箱即可生图的高质量单人人物图 prompt。`,
    ``,
    `主体描述：${subject}`,
    `目标风格：${preset.label || style}——${preset.zh}`,
    `风格关键词（请自然融入，不要堆砌）：${preset.keywords}`,
    portraitGuidance,
    ``,
    `${langInstruction}`,
    ``,
    `写作要求：`,
    `1. 严格按结构组织：[Style] + [Type] + [Content] + [Key elements]，最后另起一行 NEGATIVE 段。`,
    `   - Style：目标风格的视觉语言`,
    `   - Type：portrait / 半身像 / 写真（单人，不要画成多人或拼图）`,
    `   - Content：忠实表达主体描述（人物、动作、神态、服饰、场景），不要凭空换题材`,
    `   - Key elements：镜头 + 光照 + 构图/背景 + 配色/材质 + 画质词`,
    `2. 必须是"单人"，且人物是画面绝对主体；不要四宫格、不要拼图、不要标题文字、不要 UI。`,
    `3. 紧凑指令句，目标 120-260 字符（中文）或 30-70 词（英文）；不要 Markdown 列表、不要解释、不要寒暄。`,
    `4. 画质词（photorealistic / masterpiece / best quality / high detail / 8k 等）放在 Key elements 末尾。`,
    ``,
    `严格按下面格式输出，不要有其它任何字：`,
    ``,
    `PROMPT:`,
    `<最终人物图 prompt 主体>`,
    ``,
    `NEGATIVE:`,
    `<负面提示词，逗号分隔；用于生图时排除不想要的元素>`,
    ``,
    `STYLE_TAG: ${style}`,
    `ASPECT_HINT: <建议长宽比，如 3:4 / 9:16 / 1:1>`,
  ].join('\n');
}

async function callCodex(prompt, opts) {
  const { stdout } = await execCommand('codex', ['exec', '--skip-git-repo-check', prompt], {
    timeoutMs: opts.timeoutMs, streamStderr: opts.verbose,
  });
  return stdout;
}

async function callAgy(prompt, opts) {
  const { stdout } = await execCommand('agy', ['-p', prompt], {
    timeoutMs: opts.timeoutMs, streamStderr: opts.verbose,
  });
  return stdout;
}

// ─── 解析后端输出 ─────────────────────────────────────────────────────────────

function parseBackendOutput(text) {
  let prompt = null, negative = null, aspect = null;

  const pMatch = text.match(/PROMPT:\s*\n([\s\S]+?)(?=\n\s*(?:NEGATIVE|STYLE_TAG|ASPECT_HINT)\s*:|$)/);
  if (pMatch) prompt = pMatch[1].trim();

  const nMatch = text.match(/NEGATIVE:\s*\n?([\s\S]+?)(?=\n\s*(?:STYLE_TAG|ASPECT_HINT)\s*:|$)/);
  if (nMatch) negative = nMatch[1].trim();

  const aMatch = text.match(/ASPECT_HINT:\s*([0-9]+\s*:\s*[0-9]+)/);
  if (aMatch) aspect = aMatch[1].replace(/\s+/g, '');

  // 兜底：找不到 PROMPT 段就去噪后整段当 prompt
  if (!prompt) {
    const cleaned = text
      .split('\n')
      .filter(l => !/^(thinking|codex|tokens used|\[.*\]|hook:)/i.test(l.trim()))
      .join('\n')
      .trim();
    if (cleaned.length > 0) prompt = cleaned.slice(0, 2000);
  }

  // 清理 prompt 里混入的标签残留行
  if (prompt) {
    prompt = prompt
      .split('\n')
      .filter(l => !/^\s*(STYLE_TAG|ASPECT_HINT|NEGATIVE)\s*:/.test(l))
      .join('\n')
      .trim();
  }

  return { prompt, negative, aspect };
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
      if (!f.startsWith(yyyymmdd + '-') || !f.endsWith('.md')) continue;
      const seq = parseInt(f.slice(yyyymmdd.length + 1, -3), 10);
      if (!Number.isNaN(seq)) maxSeq = Math.max(maxSeq, seq);
    }
  } catch {}
  return resolve(PROMPTS_DIR, `${yyyymmdd}-${String(maxSeq + 1).padStart(2, '0')}.md`);
}

function buildFileContent(prompt, meta) {
  const lines = ['---'];
  lines.push(`aspect_ratio: "${meta.aspectRatio || 'auto'}"`);
  lines.push(`provider: ${meta.provider}`);
  lines.push(`source: portrait`);
  lines.push(`style: ${meta.style}`);
  if (meta.subject) lines.push(`subject: ${JSON.stringify(meta.subject)}`);
  if (meta.negative) lines.push(`negative: ${JSON.stringify(meta.negative)}`);
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
  const providers = await detectProviders();
  const provider = pickProvider(cfg.provider, providers);
  const genPrompt = buildGenerationPrompt(cfg.subject, cfg.style, cfg.lang);
  const preset = getStyle(cfg.style);

  if (cfg.dryRun) {
    const cmd = provider === 'codex' ? `codex exec --skip-git-repo-check <prompt>` : `agy -p <prompt>`;
    console.error('🧪 Dry-run — 将要调用：');
    console.error(`  Provider : ${provider}`);
    console.error(`  Command  : ${cmd}`);
    console.error(`  Subject  : ${cfg.subject}`);
    console.error(`  Style    : ${cfg.style}  (${preset.label || ''})`);
    console.error(`  Aspect   : ${cfg.aspectRatio}`);
    console.error(`  Lang     : ${cfg.lang}`);
    console.error(`  Archive  : ${cfg.archive}`);
    console.error('--- generation prompt preview ---');
    console.error(genPrompt);
    process.exit(0);
  }

  let raw = null, lastErr = null;
  for (let attempt = 1; attempt <= cfg.retries + 1; attempt++) {
    try {
      console.error(`🎨 生成中 (${provider}, style=${cfg.style}, attempt ${attempt}/${cfg.retries + 1})...`);
      raw = provider === 'codex'
        ? await callCodex(genPrompt, cfg)
        : await callAgy(genPrompt, cfg);
      break;
    } catch (err) {
      lastErr = err;
      console.error(`⚠️  第 ${attempt} 次失败：${err.message}`);
    }
  }
  if (raw == null) {
    console.error(`❌ 后端调用失败：${lastErr ? lastErr.message : 'unknown'}`);
    process.exit(1);
  }

  const parsed = parseBackendOutput(raw);
  if (!parsed.prompt) {
    console.error('❌ 后端没产出可用 prompt。加 --verbose 看原始输出。');
    process.exit(1);
  }
  const aspect = parsed.aspect || cfg.aspectRatio;

  // 输出文件 / 归档
  let outputPath = null, archivePath = null;
  const meta = {
    aspectRatio: aspect,
    provider,
    style: cfg.style,
    subject: cfg.subject,
    negative: parsed.negative,
  };
  const fileContent = buildFileContent(parsed.prompt, meta);
  if (cfg.output) {
    outputPath = resolve(process.cwd(), cfg.output);
    await writeFile(outputPath, fileContent, 'utf-8');
  }
  if (cfg.archive) {
    archivePath = await nextArchiveFilename();
    await writeFile(archivePath, fileContent, 'utf-8');
  }

  if (cfg.json) {
    console.log(JSON.stringify({
      success: true,
      provider,
      subject: cfg.subject,
      style: cfg.style,
      prompt: parsed.prompt,
      negative: parsed.negative,
      aspect_hint: aspect,
      output: outputPath,
      archive: archivePath,
    }, null, 2));
  } else {
    console.error('');
    console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.error(`✅ 生成完成 · provider=${provider} · style=${cfg.style} · ar=${aspect}`);
    if (parsed.negative) console.error(`🚫 负面提示：${parsed.negative}`);
    if (outputPath) console.error(`📄 已写入：${outputPath}`);
    if (archivePath) console.error(`🗄  已归档：${archivePath}`);
    console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    // PROMPT 本体打到 stdout，方便 pipe 给 generate-image.js
    console.log(parsed.prompt);
  }
}

main().catch(err => { console.error(`❌ ${err.message}`); process.exit(1); });

