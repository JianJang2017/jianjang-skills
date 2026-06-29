#!/usr/bin/env node

/**
 * Reverse-engineer a text-to-image prompt from an existing image.
 *
 * Backends: codex-cli, agy (Antigravity / Gemini)
 *
 * 用法 (Usage):
 *   reverse-prompt.js --image cover.png
 *   reverse-prompt.js --image cover.png --output reversed.md --archive
 *   reverse-prompt.js --image cover.png --provider agy --lang zh
 *
 * 输出 (Output):
 *   - 默认打印到 stdout（最后一行是 JSON，便于程序消费）
 *   - --output 写入文件（带 frontmatter + PROMPT: 块，与 prompts/ 一致）
 *   - --archive 自动归档到 ../prompts/YYYYMMDD-NN.md（标记 source: reverse）
 *
 * 设计目标：
 *   反推出来的 prompt 直接能喂回 generate-image.js，所以输出格式保持和
 *   prompts/ 下归档文件一致 —— 这样 reverse → (optional optimize) → generate
 *   是一条顺滑的流水线。
 */

import { spawn } from 'node:child_process';
import { readFile, writeFile, stat, mkdir, readdir } from 'node:fs/promises';
import { resolve, dirname, basename, join } from 'node:path';
import { homedir, tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROMPTS_DIR = resolve(__dirname, '..', 'prompts');

const DEFAULTS = {
  provider: 'auto',
  lang: 'zh',                 // zh (默认) | en | auto
  timeoutMs: 3 * 60 * 1000,   // 3 分钟够看图回答了
  retries: 1,
};

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    image: null,
    output: null,
    provider: DEFAULTS.provider,
    lang: DEFAULTS.lang,
    archive: false,
    timeoutMs: DEFAULTS.timeoutMs,
    retries: DEFAULTS.retries,
    aspectRatio: null,         // 仅用于归档时写 frontmatter；不指定就 "auto"
    verbose: false,
    dryRun: false,
    json: false,               // 只输出 JSON（机器消费）
    ignoreUi: true,            // 默认忽略 App/系统 UI（状态栏、按钮、点赞数等）
  };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    switch (a) {
      case '--image': case '-i': cfg.image = args[++i]; break;
      case '--output': case '-o': cfg.output = args[++i]; break;
      case '--provider': case '-p': cfg.provider = args[++i]; break;
      case '--lang': case '-l': cfg.lang = args[++i]; break;
      case '--archive': cfg.archive = true; break;
      case '--aspect-ratio': case '--ar': cfg.aspectRatio = args[++i]; break;
      case '--timeout': cfg.timeoutMs = parseInt(args[++i], 10) * 1000; break;
      case '--retries': cfg.retries = parseInt(args[++i], 10); break;
      case '--verbose': case '-v': cfg.verbose = true; break;
      case '--dry-run': cfg.dryRun = true; break;
      case '--json': cfg.json = true; break;
      case '--ignore-ui': cfg.ignoreUi = true; break;
      case '--keep-ui': cfg.ignoreUi = false; break;
      case '--help': case '-h': showHelp(); process.exit(0);
      default:
        if (!cfg.image && !a.startsWith('-')) cfg.image = a;
    }
  }
  if (!cfg.image) {
    console.error('Error: --image is required');
    showHelp(); process.exit(1);
  }
  return cfg;
}

function showHelp() {
  console.log(`
Reverse-prompt — 从图片反推生图 prompt

Usage:
  reverse-prompt.js --image <path> [options]

Options:
  --image, -i <path>           源图片路径（必填）
  --output, -o <path>          反推 prompt 输出文件（带 frontmatter）
  --provider, -p <auto|codex|agy>  后端选择 (default: auto)
  --lang, -l <zh|en|auto>      输出语言 (default: zh —— 中文主体，技术词英文)
  --archive                    自动归档到 prompts/YYYYMMDD-NN.md
  --aspect-ratio, --ar <W:H>   归档/输出文件中的 aspect_ratio 字段
  --ignore-ui                  忽略 App/系统 UI 元素（状态栏、按钮、计数、水印），
                               只反推画面主体本身（default: ON）
  --keep-ui                    保留并复刻 UI 元素（截图复刻场景下使用）
  --timeout <seconds>          后端调用超时 (default: 180)
  --retries <n>                失败重试次数 (default: 1)
  --verbose, -v                透传后端 stderr
  --dry-run                    只打印将要调用的命令，不实际跑
  --json                       仅输出最终 JSON 结果（其他日志走 stderr）
  --help, -h                   显示本帮助

输出格式：
  反推出来的 prompt 默认按 [Style] + [Type] + [Content] + [Key elements]
  结构组织，可直接喂回 generate-image.js / optimize-prompt.js。

Examples:
  # 看图说话，结果打到 stdout（默认忽略 UI）
  reverse-prompt.js -i cover.png

  # 反推 + 归档到 prompts/
  reverse-prompt.js -i cover.png --archive --ar 3:4

  # 截图复刻场景：保留 App UI 文字 / 按钮
  reverse-prompt.js -i screenshot.png --keep-ui

  # 用 agy 后端，输出到文件
  reverse-prompt.js -i cover.png -p agy -o reversed.md
`);
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
    throw new Error('没找到可用的后端 (codex / agy)。请先安装其中之一。');
  }
  // 兼容 gemini 旧名
  if (requested === 'gemini') requested = 'agy';
  if (!available[requested]) throw new Error(`后端 "${requested}" 不可用。已安装的：${Object.keys(available).filter(k => available[k]).join(', ') || '(无)'}`);
  return requested;
}

// ─── Prompt 模板 ────────────────────────────────────────────────────────────

function buildAnalysisPrompt(imageAbsPath, lang, ignoreUi) {
  const langInstruction = (() => {
    if (lang === 'en') return 'Output the reverse-engineered prompt in English.';
    if (lang === 'auto') return '如图中含明显英文文字或主体是英文海报/图表，则用英文输出；否则用中文输出（技术词保留英文）。';
    // zh
    return '用中文输出反推的 prompt，技术词（如 React/PostgreSQL/3D/UI）保留英文。';
  })();

  // UI 屏蔽指令：默认 ON。这是反推 App/系统截图时的关键一步——状态栏（时间、信号、
  // 电量）、顶导（Tab 名）、悬浮按钮、点赞/评论/收藏计数、@用户名、水印、底部
  // 导航条 等等，都不是原始生图 prompt 的一部分；如果让模型照搬进 PROMPT，下次
  // 生图就会把这些 UI 元素也"画"出来，毁掉效果。
  const uiInstruction = ignoreUi
    ? [
        ``,
        `**重要：忽略图中所有的 App / 系统 UI 元素**——不要把它们写进反推的 PROMPT 段。`,
        `要忽略的内容包括但不限于：`,
        `- 顶部状态栏（时间、信号格、Wi-Fi、电量、运营商）`,
        `- App 顶部导航（Tab 名如「直播/团购/关注/推荐」、搜索图标、菜单图标）`,
        `- 悬浮按钮 / 计数（点赞 ♥、评论 💬、收藏 ⭐、分享、关注按钮及其旁的数字）`,
        `- @用户名 标识、话题 #xxx 标签、作者声明角标、广告/推荐标签`,
        `- 系统底部导航栏、虚拟按键（圆/方/三角）、Home indicator`,
        `- 任何水印、二维码、弹幕条`,
        `把图当作"如果没有这些 UI 叠加层，原始画面应该长什么样"来反推。`,
        `Style/Type 段也不要写"截图"或"短视频截图"——直接按底层画面的真实类型来写`,
        `（例如"插画"/"摄影"/"3D 渲染"）。`,
      ].join('\n')
    : [
        ``,
        `**保留 UI 元素**：图中如果有 App/系统 UI 文字或按钮，按原样写进反推的 PROMPT 段`,
        `（用引号保留原文，不要翻译）。这是「截图复刻」场景，UI 也是画面一部分。`,
      ].join('\n');

  return [
    `你是一名提示词反推专家。请仔细查看下面这张图片，反推出"用文生图模型最有可能生成它的那条 prompt"。`,
    ``,
    `图片路径（绝对路径，请直接读取）：${imageAbsPath}`,
    uiInstruction,
    ``,
    `${langInstruction}`,
    ``,
    `按以下结构组织（紧凑，单段或两段，避免大段散文）：`,
    `[Style] + [Type] + [Content] + [Key elements]`,
    `——即：风格 + 图像类型（如 infographic / 流程图 / 摄影 / 插画 / 渲染） + 主体内容 + 关键元素（构图、配色、材质、光照、文字）。`,
    ``,
    `要求：`,
    `1. 一次性、紧凑、可直接复用为生图 prompt；目标 100-220 字符。`,
    `2. 不要写"这是一张……"这种描述句，要写"生成 X 风格的 Y，包含 Z"这种指令句。`,
    `3. 不要带 Markdown 列表、不要带表情、不要解释、不要寒暄。`,
    ignoreUi
      ? `4. 不要在 PROMPT 中提及任何 UI 元素（参考上面的"忽略"列表）；画面里如果有海报/招牌/书页这类"内容性文字"才保留并用引号原样写出。`
      : `4. 如果图里有可识别文字（含 UI 文字），原样保留（用引号包起来），不要翻译。`,
    `5. 注意配色（warm cream / black lines / pastel blocks 这类表达可直接保留英文）。`,
    ``,
    `严格按下面的格式输出，不要有其它任何字：`,
    ``,
    `PROMPT:`,
    `<反推出来的 prompt 主体>`,
    ``,
    `STYLE_TAG: <一两个词概括风格，如 hand-drawn / blueprint / watercolor / cyberpunk / 3d / healing / photo / minimal>`,
    `ASPECT_HINT: <根据图像看起来的长宽比给一个建议，如 16:9 / 3:4 / 1:1>`,
  ].join('\n');
}

// ─── 后端调用 ───────────────────────────────────────────────────────────────

async function callCodex(analysisPrompt, opts) {
  // codex exec 接受 prompt 文本，能读绝对路径下的图片文件（具备文件系统访问）
  const { stdout } = await execCommand('codex', ['exec', '--skip-git-repo-check', analysisPrompt], {
    timeoutMs: opts.timeoutMs,
    streamStderr: opts.verbose,
  });
  return stdout;
}

async function callAgy(analysisPrompt, opts) {
  const { stdout } = await execCommand('agy', ['-p', analysisPrompt], {
    timeoutMs: opts.timeoutMs,
    streamStderr: opts.verbose,
  });
  return stdout;
}

// ─── 解析后端输出 ───────────────────────────────────────────────────────────

function parseBackendOutput(rawOutput) {
  // 我们要求后端按 PROMPT: ... STYLE_TAG: ... ASPECT_HINT: ... 输出。
  // 但 codex/agy 经常会前后裹一层 "已生成"/"思考过程" 文本，所以用区段匹配。

  const text = rawOutput.replace(/\r\n/g, '\n');

  let prompt = null;
  let style = null;
  let aspect = null;

  // PROMPT 区段：从 "PROMPT:" 到下一个全大写标签（STYLE_TAG / ASPECT_HINT）或字符串结尾
  const pMatch = text.match(/PROMPT:\s*\n?([\s\S]+?)(?=\n\s*(?:STYLE_TAG|ASPECT_HINT)\s*:|\Z)/);
  if (pMatch) prompt = pMatch[1].trim();

  const sMatch = text.match(/STYLE_TAG:\s*([^\n]+)/);
  if (sMatch) style = sMatch[1].trim();

  const aMatch = text.match(/ASPECT_HINT:\s*([^\n]+)/);
  if (aMatch) aspect = aMatch[1].trim();

  // 兜底：如果完全找不到 PROMPT 段，把整段后端输出去掉常见噪声后当作 prompt
  if (!prompt) {
    const cleaned = text
      .split('\n')
      .filter(l => !/^(thinking|codex|tokens used|\[.*\])/i.test(l.trim()))
      .join('\n')
      .trim();
    if (cleaned.length > 0) prompt = cleaned.slice(0, 2000);
  }

  // 清理 prompt 里可能混入的 STYLE_TAG/ASPECT_HINT 残留行
  if (prompt) {
    prompt = prompt
      .split('\n')
      .filter(l => !/^\s*(STYLE_TAG|ASPECT_HINT)\s*:/.test(l))
      .join('\n')
      .trim();
  }

  return { prompt, style, aspect };
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
      if (!f.startsWith(today.getFullYear() + '') || !f.endsWith('.md')) continue;
      const m = f.match(/^(\d{8})-(\d{2})\.md$/);
      if (!m || m[1] !== yyyymmdd) continue;
      maxSeq = Math.max(maxSeq, parseInt(m[2], 10));
    }
  } catch {}
  const next = String(maxSeq + 1).padStart(2, '0');
  return join(PROMPTS_DIR, `${yyyymmdd}-${next}.md`);
}

function buildFileContent(prompt, meta) {
  const lines = ['---'];
  lines.push(`aspect_ratio: "${meta.aspectRatio || 'auto'}"`);
  lines.push(`provider: ${meta.provider}`);
  lines.push(`source: reverse`);
  if (meta.sourceImage) lines.push(`source_image: ${meta.sourceImage}`);
  if (meta.style) lines.push(`style_tag: ${meta.style}`);
  if (typeof meta.ignoreUi === 'boolean') lines.push(`ignore_ui: ${meta.ignoreUi}`);
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

  if (!(await exists(cfg.image))) {
    console.error(`❌ 图片不存在：${cfg.image}`);
    process.exit(1);
  }
  const imageAbs = resolve(cfg.image);

  const providers = await detectProviders();
  const provider = await pickProvider(cfg.provider, providers);

  const analysisPrompt = buildAnalysisPrompt(imageAbs, cfg.lang, cfg.ignoreUi);

  if (cfg.dryRun) {
    const cmd = provider === 'codex'
      ? `codex exec --skip-git-repo-check <prompt>`
      : `agy -p <prompt>`;
    console.error('🧪 Dry-run — 将要调用：');
    console.error(`  Provider : ${provider}`);
    console.error(`  Command  : ${cmd}`);
    console.error(`  Image    : ${imageAbs}`);
    console.error(`  Lang     : ${cfg.lang}`);
    console.error(`  Ignore UI: ${cfg.ignoreUi}`);
    console.error(`  Archive  : ${cfg.archive}`);
    console.error('--- analysis prompt preview ---');
    console.error(analysisPrompt);
    process.exit(0);
  }

  // 实际调用 + 重试
  let raw = null;
  let lastErr = null;
  const maxAttempts = cfg.retries + 1;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    if (!cfg.json) {
      console.error(`🔍 反推中 (${provider}, attempt ${attempt}/${maxAttempts})...`);
    }
    try {
      raw = provider === 'codex'
        ? await callCodex(analysisPrompt, cfg)
        : await callAgy(analysisPrompt, cfg);
      break;
    } catch (e) {
      lastErr = e;
      if (!cfg.json) console.error(`⚠️  ${e.message}`);
    }
  }
  if (raw === null) {
    console.error(`❌ 反推失败：${lastErr?.message || 'unknown'}`);
    if (cfg.json) console.log(JSON.stringify({ success: false, error: lastErr?.message || 'unknown' }));
    process.exit(1);
  }

  const parsed = parseBackendOutput(raw);
  if (!parsed.prompt) {
    console.error('❌ 后端没有产出可解析的 PROMPT 段');
    if (cfg.verbose) console.error(raw.slice(-2000));
    process.exit(1);
  }

  // 写文件 / 归档
  let outputPath = null;
  let archivePath = null;
  const meta = {
    aspectRatio: cfg.aspectRatio,
    provider,
    sourceImage: imageAbs,
    style: parsed.style,
    ignoreUi: cfg.ignoreUi,
  };
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

  // 输出
  if (cfg.json) {
    console.log(JSON.stringify({
      success: true,
      provider,
      prompt: parsed.prompt,
      style: parsed.style,
      aspect_hint: parsed.aspect,
      source_image: imageAbs,
      ignore_ui: cfg.ignoreUi,
      output: outputPath,
      archive: archivePath,
    }, null, 2));
  } else {
    console.error('');
    console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.error(
      `✅ 反推完成 · provider=${provider}` +
      (parsed.style ? ` · style=${parsed.style}` : '') +
      (parsed.aspect ? ` · ar=${parsed.aspect}` : '') +
      ` · ${cfg.ignoreUi ? 'ignore-ui' : 'keep-ui'}`
    );
    if (outputPath) console.error(`📄 已写入：${outputPath}`);
    if (archivePath) console.error(`🗄  已归档：${archivePath}`);
    console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    // PROMPT 本体打到 stdout，方便 pipe
    console.log(parsed.prompt);
  }
  process.exit(0);
}

main().catch(err => {
  console.error('❌ Fatal:', err.message);
  process.exit(1);
});
