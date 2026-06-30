#!/usr/bin/env node

/**
 * Publish a note (image + title + body + topics) to Xiaohongshu (RedNote)
 * via a persistent Playwright Chromium session.
 *
 * Design goals:
 *  - Self-contained: no OpenClaw / claw CLI needed. Just Playwright Chromium.
 *  - Persistent login: first run scans a QR code, later runs reuse the session.
 *  - Safe by default: fill everything, then STOP at the publish button and
 *    screenshot. Only --publish actually clicks publish.
 *
 * Usage:
 *   node scripts/publish_xiaohongshu.js \
 *     --image cover.png \
 *     --title "标题<=20字" \
 *     --content "正文文本" \
 *     --topics "AI,效率"
 *
 *   # multi-image, body from file, auto-publish:
 *   node scripts/publish_xiaohongshu.js \
 *     --image a.png,b.png --title "x" --content-file body.md --publish
 *
 *   # preview only (no browser):
 *   node scripts/publish_xiaohongshu.js --image x.png --title "x" --content "y" --dry-run
 */

// NOTE: playwright is imported lazily inside main() (dynamic import) so that
// --dry-run / --help / arg-validation work even before the package is installed.
import { readFile, writeFile, mkdir, access, readdir, stat, copyFile, unlink } from 'node:fs/promises';
import { resolve, join, dirname, extname } from 'node:path';
import { homedir, tmpdir } from 'node:os';
import { spawn } from 'node:child_process';
import { inflateSync } from 'node:zlib';

// ─── Config ─────────────────────────────────────────────────────────────────

const DEFAULTS = {
  publishUrl: 'https://creator.xiaohongshu.com/publish/publish?source=official',
  loginUrl: 'https://creator.xiaohongshu.com/login',
  userDataDir: join(homedir(), '.image-factory-skill', 'xhs-profile'),
  stepTimeout: 30000,        // per-step timeout (ms)
  loginTimeout: 180000,      // wait up to 3 min for QR scan
  titleMaxLen: 20,           // XHS title hard cap
  genTimeoutMs: 5 * 60 * 1000, // image generation timeout (5 min)
};

// 同目录下的生图脚本 + codex 兜底目录（与 send_feishu_image.py 对齐）
const SCRIPT_DIR = dirname(new URL(import.meta.url).pathname);
const SKILL_DIR = dirname(SCRIPT_DIR);
const PROMPTS_DIR = join(SKILL_DIR, 'prompts');
const GENERATE_IMAGE_JS = join(SCRIPT_DIR, 'generate-image.js');
const CODEX_GENERATED_DIR = join(homedir(), '.codex', 'generated_images');

// ─── Selectors (MAINTENANCE POINT) ──────────────────────────────────────────
// XHS revamps its creator UI fairly often. When a step starts failing, this is
// the FIRST place to update. Each key holds an ordered list of candidate
// selectors — the script tries them in order and uses the first that matches.
// Keep the most specific/stable selector first.

const SELECTORS = {
  // "已登录" 信号：出现这些任意一个即视为登录态有效
  loggedIn: [
    'text=发布笔记',
    'text=上传图文',
    '.creator-tab',
    '.header .user, .user-avatar, .avatar',
  ],
  // 登录页二维码
  qrcode: [
    '.qrcode-img img',
    '.css-qrcode img',
    'img[src*="qrcode"]',
    '.login-qrcode img',
  ],
  // 发布页「上传图文」tab（默认进来可能是视频 tab）
  imageTextTab: [
    'text=上传图文',
    '.creator-tab:has-text("图文")',
    'div[role="tab"]:has-text("图文")',
  ],
  // 图片上传 input（隐藏的 <input type=file>）——改版后视频/图片 input 可能并存，
  // 优先挑 accept 含图片格式的那个，避免误喂到视频 input。
  uploadInput: [
    'input[type=file][accept*="png"]',
    'input[type=file][accept*="jpg"]',
    'input[type=file][accept*="image"]',
    '.upload-input input[type=file]',
    'input[type=file]',
  ],
  // 进入编辑页的信号：标题输入框出现
  titleInput: [
    'input[placeholder*="标题"]',
    '.title-input input',
    'input.d-text',
    'textarea[placeholder*="标题"]',
  ],
  // 正文编辑区（contenteditable）
  contentEditor: [
    'div[contenteditable="true"]',
    '.ql-editor',
    '.content-input[contenteditable]',
    '#post-textarea',
  ],
  // 话题下拉候选项（输入 #xxx 后弹出）
  topicOption: [
    '.mention-list .item',
    '.topic-item',
    '.dropdown-item',
    'li[role="option"]',
  ],
  // 发布按钮：改版后是自定义 web component <xhs-publish-btn>，shadowRoot 为 closed，
  // 内部 button 无法用常规 selector / 穿透定位拿到。host 上有属性：
  //   submit-text="发布" save-text="暂存离开" submit-disabled="false"
  // 所以这里用 host 元素作为定位锚点，点击时落在 host 右侧（「发布」主按钮区域）。
  // 旧版按钮（button:has-text("发布") 等）保留为兜底候选。
  publishButton: [
    'xhs-publish-btn',
    'button:has-text("发布")',
    '.publishBtn',
    '.submit button',
    'button.publish',
  ],
  // 发布成功信号
  publishSuccess: [
    'text=发布成功',
    'text=发布成功，',
    '.success-toast',
  ],
  // 「添加内容类型声明」下拉入口（表单底部，d-select 组件）
  declareEntry: [
    'div.d-select-main:has-text("添加内容类型声明")',
    'div.d-select-wrapper:has-text("添加内容类型声明")',
    'div.wrapper:has-text("添加内容类型声明")',
  ],
  // 下拉里「笔记含AI合成内容」选项（注意是「合成」不是「生成」）
  declareAIOption: [
    '.d-grid-item:has-text("笔记含AI合成内容")',
    'div:has-text("笔记含AI合成内容")',
    'text=笔记含AI合成内容',
  ],
};

// ─── Argument parsing ───────────────────────────────────────────────────────
// Hand-rolled parser to match the style of generate-image.js (no extra deps).

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    images: [],
    prompt: null,           // NEW: 直接给文字 prompt，先生图再发布
    provider: 'auto',       // NEW: 生图后端 auto|codex|gemini
    aspectRatio: '3:4',     // NEW: 生图宽高比（小红书竖图友好，默认 3:4）
    output: null,           // NEW: 生成图片保存路径（缺省用临时文件）
    count: 1,               // NEW: 同一 prompt 生成 N 张不同图，作为一条多图笔记发布
    title: null,
    content: null,
    contentFile: null,
    promptFile: null,       // 用于自动推导 title/content（也可作为生图来源）
    topics: [],
    aiDeclare: true,        // 默认选「内容类型声明=笔记含AI合成内容」；--no-ai-declare 关闭
    publish: false,
    headed: false,
    userDataDir: process.env.XHS_USER_DATA_DIR || DEFAULTS.userDataDir,
    screenshot: null,
    timeout: DEFAULTS.stepTimeout,
    dryRun: false,
    help: false,
  };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    switch (a) {
      case '--image': case '-i':
        // 支持逗号分隔，也支持多次传入
        cfg.images.push(...args[++i].split(',').map((s) => s.trim()).filter(Boolean));
        break;
      case '--prompt': case '-P': cfg.prompt = args[++i]; break;          // NEW
      case '--provider': cfg.provider = args[++i]; break;                  // NEW
      case '--aspect-ratio': case '--ar': cfg.aspectRatio = args[++i]; break; // NEW
      case '--output': case '-o': cfg.output = args[++i]; break;           // NEW
      case '--count': case '-n': cfg.count = Math.max(1, parseInt(args[++i], 10) || 1); break; // NEW
      case '--title': case '-t': cfg.title = args[++i]; break;
      case '--content': case '-c': cfg.content = args[++i]; break;
      case '--content-file': cfg.contentFile = args[++i]; break;
      case '--prompt-file': cfg.promptFile = args[++i]; break;
      case '--topics':
        cfg.topics.push(...args[++i].split(',').map((s) => s.trim().replace(/^#/, '')).filter(Boolean));
        break;
      case '--publish': cfg.publish = true; break;
      case '--no-ai-declare': cfg.aiDeclare = false; break;
      case '--headed': cfg.headed = true; break;
      case '--user-data-dir': cfg.userDataDir = args[++i]; break;
      case '--screenshot': cfg.screenshot = args[++i]; break;
      case '--timeout': cfg.timeout = parseInt(args[++i], 10) || DEFAULTS.stepTimeout; break;
      case '--dry-run': cfg.dryRun = true; break;
      case '--help': case '-h': cfg.help = true; break;
      default:
        if (a.startsWith('-')) {
          console.error(`⚠️  未知参数: ${a}`);
        }
    }
  }
  return cfg;
}

function printHelp() {
  console.log(`
小红书图文笔记发布（Playwright）

用法:
  # A. 发已有图
  node scripts/publish_xiaohongshu.js --image <图> [--title <标题>] [--content <正文>] [选项]
  # B. 生成即发布（无 --image，先生图再发）
  node scripts/publish_xiaohongshu.js --prompt "<生图描述>" [--title ...] [选项]

图片来源（二选一）:
  --image, -i <路径>       已有图，逗号分隔或多次传入（首图=封面）
  --prompt, -P <文本>      生图描述：无 --image 时先调 generate-image.js 生成再发布
  --prompt-file <路径>     prompt 文件（prompts/YYYYMMDD-NN.md）：可作生图来源，
                           也用于在缺 --title/--content 时自动推导

生图选项（仅在用 --prompt/--prompt-file 生成时有效）:
  --provider <auto|codex|gemini>  生图后端（默认 auto）
  --aspect-ratio, --ar <W:H>      宽高比（默认 3:4，小红书竖图友好）
  --output, -o <路径>             生成图保存路径（默认临时文件）
  --count, -n <N>                 同一 prompt 生成 N 张不同图，作为一条多图笔记发布（默认 1）

标题与正文（缺省可由 prompt 自动推导）:
  --title, -t <文本>       标题（<=${DEFAULTS.titleMaxLen} 字，强校验）；缺省时按图片风格自动生成
  --content, -c <文本>     正文文本
  --content-file <路径>    从文件读正文

可选:
  --topics <a,b,c>         话题，逗号分隔（不带 #，脚本自动加）
  --publish                自动点击发布（默认仅停在发布按钮，等人工确认）
  --no-ai-declare          不选「笔记含AI合成内容」声明（默认会选，AI内容合规更稳妥）
  --headed                 显示浏览器窗口（首次登录/调试；未登录时自动开启）
  --user-data-dir <目录>   持久化登录态目录（默认 ~/.image-factory-skill/xhs-profile）
  --screenshot <路径>      停手时截图保存路径（默认 /tmp/xhs-publish-<ts>.png）
  --timeout <毫秒>         单步超时（默认 ${DEFAULTS.stepTimeout}）
  --dry-run                预览参数与步骤，不启动浏览器/不生图
  --help, -h               显示帮助

环境变量:
  XHS_USER_DATA_DIR        等价于 --user-data-dir

一条龙：--prompt 生图 → 自动归档 prompt → 自动推导标题/正文 → 发布（默认停在发布按钮）。
自动推导：标题取自图片画风（手绘/水彩/科技感…），正文取自 prompt 精简版。
显式 --title / --content 永远优先于自动推导。
安全：默认填好内容后停在「发布」按钮并截图，由你人工确认后点击发布。
`);
}

// ─── Helpers ────────────────────────────────────────────────────────────────

const log = (msg) => console.log(msg);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function fileExists(p) {
  try { await access(p); return true; } catch { return false; }
}

// ─── Prompt → title/content derivation ──────────────────────────────────────
// 与 generate-image.js / send_feishu_image.py 的解析保持一致：优先取 PROMPT: 段，
// 否则剥离 --- frontmatter 后取全文。返回纯 prompt 文本（失败返回 null）。
async function readPromptFile(path) {
  let content;
  try {
    content = await readFile(resolve(path), 'utf8');
  } catch {
    return null;
  }
  // 用 [\s\S] + 末尾边界，避免把多段 prompt 截断成第一段
  const m = content.match(/^PROMPT:\s*\n([\s\S]+?)(?=\n---|\n##\s|$)/m);
  if (m) return m[1].trim();

  // 没有 PROMPT: 标记则剥离 frontmatter 后取全文
  const lines = content.split('\n');
  let inFm = false;
  const body = [];
  for (const line of lines) {
    if (line.trim() === '---') { inFm = !inFm; continue; }
    if (!inFm) body.push(line);
  }
  const text = body.join('\n').trim();
  return text || null;
}

// ─── Image generation (生成即发布) ───────────────────────────────────────────
// 复用同目录 generate-image.js（与 send_feishu_image.py 同一套后端）。
// 流程：写临时 prompt md → 调 generate-image.js → 校验产物 →（兜底捞 codex 图）→ 归档 prompt。

/** 把进程跑起来并带超时，resolve {code, stdout, stderr}。 */
function execCommand(command, cmdArgs, timeoutMs) {
  return new Promise((res) => {
    const child = spawn(command, cmdArgs, { stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '', stderr = '';
    const timer = setTimeout(() => { child.kill('SIGKILL'); }, timeoutMs);
    child.stdout.on('data', (d) => { stdout += d; });
    child.stderr.on('data', (d) => { stderr += d; });
    child.on('close', (code) => { clearTimeout(timer); res({ code, stdout, stderr }); });
    child.on('error', (e) => { clearTimeout(timer); res({ code: -1, stdout, stderr: stderr + e.message }); });
  });
}

/** 兜底：generate-image.js 失败/超时但 codex 已落盘时，捞 sinceTs 之后最新的图复制到 output。
 *  注意：codex 把图写在会话子目录 ~/.codex/generated_images/<session>/xxx.png，
 *  所以必须递归子目录，不能只扫顶层（早期 bug：只扫顶层导致永远捞不到、误报生成失败）。 */
async function recoverCodexImage(output, sinceTs) {
  let newest = null;
  async function walk(dir) {
    let entries;
    try { entries = await readdir(dir, { withFileTypes: true }); } catch { return; }
    for (const ent of entries) {
      const full = join(dir, ent.name);
      if (ent.isDirectory()) { await walk(full); continue; }
      if (!ent.isFile() || !/\.(png|jpe?g|webp)$/i.test(ent.name)) continue;
      try {
        const st = await stat(full);
        if (st.mtimeMs < sinceTs || st.size < 1024) continue;
        if (!newest || st.mtimeMs > newest.mtime) newest = { path: full, mtime: st.mtimeMs };
      } catch { /* skip */ }
    }
  }
  await walk(CODEX_GENERATED_DIR);
  if (!newest) return null;
  try {
    await mkdir(dirname(resolve(output)), { recursive: true });
    await copyFile(newest.path, output);
    return output;
  } catch {
    return newest.path; // output 不可写时退回源图
  }
}

/** 把 prompt 归档到 prompts/YYYYMMDD-NN.md（与 send_feishu_image.py 命名一致）。返回路径或 null。 */
async function archivePrompt(promptText, aspectRatio, provider) {
  if (!promptText) return null;
  try {
    await mkdir(PROMPTS_DIR, { recursive: true });
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    let maxSeq = 0;
    try {
      for (const f of await readdir(PROMPTS_DIR)) {
        const m = f.match(new RegExp(`^${today}-(\\d+)\\.md$`));
        if (m) maxSeq = Math.max(maxSeq, parseInt(m[1], 10));
      }
    } catch { /* dir 刚建 */ }
    const filename = `${today}-${String(maxSeq + 1).padStart(2, '0')}.md`;
    const filepath = join(PROMPTS_DIR, filename);
    const fm = `---\naspect_ratio: "${aspectRatio}"\nprovider: ${provider}\ntimestamp: ${new Date().toISOString()}\n---\n\n`;
    await writeFile(filepath, `${fm}PROMPT:\n${promptText}\n`, 'utf8');
    return filepath;
  } catch {
    return null;
  }
}

/** 调 generate-image.js 生成图片。返回 { ok, path|message }。成功后归档 prompt。 */
async function generateImage(promptText, output, aspectRatio, provider) {
  if (!(await fileExists(GENERATE_IMAGE_JS))) {
    return { ok: false, message: `找不到生图脚本: ${GENERATE_IMAGE_JS}` };
  }
  const sinceTs = Date.now() - 5000; // 容忍少量时钟/启动延迟
  const promptFile = join(tmpdir(), `xhs-genprompt-${Date.now()}.md`);
  try {
    await writeFile(promptFile, `---\naspect_ratio: "${aspectRatio}"\n---\n\nPROMPT:\n${promptText}\n`, 'utf8');
    log(`🎨 生成图片中…（provider=${provider}, ar=${aspectRatio}）`);
    const { code, stdout, stderr } = await execCommand('node', [
      GENERATE_IMAGE_JS, '--prompt-file', promptFile, '--output', output,
      '--aspect-ratio', aspectRatio, '--provider', provider,
    ], DEFAULTS.genTimeoutMs);

    // 正常成功
    if (code === 0 && (await fileExists(output)) && (await stat(output)).size > 0) {
      const archived = await archivePrompt(promptText, aspectRatio, provider);
      if (archived) log(`📝 Prompt 已归档: ${archived.split('/').pop()}`);
      return { ok: true, path: output };
    }
    // 兜底：脚本失败/超时但 codex 已落盘
    const tail = (stderr || stdout).trim().slice(-300);
    const recovered = await recoverCodexImage(output, sinceTs);
    if (recovered) {
      log(`⚠️  生图脚本报错/超时，已从 codex 目录兜底捞回：${recovered}`);
      const archived = await archivePrompt(promptText, aspectRatio, provider);
      if (archived) log(`📝 Prompt 已归档: ${archived.split('/').pop()}`);
      return { ok: true, path: recovered };
    }
    return { ok: false, message: code !== 0 ? `图片生成失败: ${tail}` : `脚本成功但产物无效: ${output}` };
  } catch (e) {
    return { ok: false, message: `生图异常: ${e.message}` };
  } finally {
    await unlink(promptFile).catch(() => {});
  }
}

/** 在扩展名前插入序号后缀：suffixOutput('cover.png', 2) → 'cover-2.png'。
 *  与 generate-image.js 的 --count 命名保持一致，用于 JSON 解析失败时的磁盘兜底。 */
function suffixOutput(output, index) {
  const ext = extname(output);
  const base = ext ? output.slice(0, -ext.length) : output;
  return `${base}-${index}${ext}`;
}

/** 生成 N 张图（同一 prompt，-n 张不同图）。返回 { ok, paths|message }。
 *  count<=1 退回单图 generateImage（保留 codex 兜底）。count>1 调
 *  generate-image.js --count N，解析末行 JSON 的 outputs 拿全部产物路径。
 *  只要至少有一张成功即视为成功，paths 为成功列表。 */
async function generateImages(promptText, output, count, aspectRatio, provider) {
  if (count <= 1) {
    const res = await generateImage(promptText, output, aspectRatio, provider);
    return res.ok ? { ok: true, paths: [res.path] } : res;
  }

  if (!(await fileExists(GENERATE_IMAGE_JS))) {
    return { ok: false, message: `找不到生图脚本: ${GENERATE_IMAGE_JS}` };
  }
  const promptFile = join(tmpdir(), `xhs-genprompt-${Date.now()}.md`);
  try {
    await writeFile(promptFile, `---\naspect_ratio: "${aspectRatio}"\n---\n\nPROMPT:\n${promptText}\n`, 'utf8');
    log(`🎨 生成 ${count} 张图片中…（provider=${provider}, ar=${aspectRatio}）`);
    // 超时按张数放大：N 张图最坏要 N×单图耗时（并发也可能排队），用固定 5 分钟会在
    // 子进程打印最终 JSON 前就被 SIGKILL，导致解析不到 outputs（误报"均未产出"）。
    const genTimeout = DEFAULTS.genTimeoutMs * count;
    const { code, stdout, stderr } = await execCommand('node', [
      GENERATE_IMAGE_JS, '--prompt-file', promptFile, '--output', output,
      '--aspect-ratio', aspectRatio, '--provider', provider, '--count', String(count),
    ], genTimeout);

    // 解析末行 JSON 的 outputs 字段
    const lines = (stdout || '').trim().split('\n');
    let data = null;
    for (let i = lines.length - 1; i >= 0; i--) {
      const line = lines[i].trim();
      if (line.startsWith('{') && line.endsWith('}')) {
        try { data = JSON.parse(line); break; } catch {}
      }
    }
    let candidates = ((data && data.outputs) || []).filter(p => p);
    // 兜底：JSON 没解析到（子进程被超时杀掉、stdout 截断等），直接按 -1..-N 后缀扫磁盘。
    // generate-image.js 即使被 SIGKILL，已落盘的图仍在 output 的 -1..-N 路径上。
    if (candidates.length === 0) {
      candidates = Array.from({ length: count }, (_, i) => suffixOutput(output, i + 1));
    }
    const existing = [];
    for (const p of candidates) {
      if (await fileExists(p)) existing.push(p);
    }

    if (existing.length > 0) {
      const archived = await archivePrompt(promptText, aspectRatio, provider);
      if (archived) log(`📝 Prompt 已归档: ${archived.split('/').pop()}`);
      if (existing.length < count) {
        log(`⚠️  请求 ${count} 张，实际成功 ${existing.length} 张，继续用已成功的图发布。`);
      }
      return { ok: true, paths: existing };
    }

    const tail = (stderr || stdout).trim().slice(-300);
    return { ok: false, message: `图片生成失败（${count} 张均未产出）: ${tail}` };
  } catch (e) {
    return { ok: false, message: `生图异常: ${e.message}` };
  } finally {
    await unlink(promptFile).catch(() => {});
  }
}

// 风格词库：从 prompt 里识别画风，用于生成标题。顺序≈优先级。
// 注意：detectStyle 用 includes 匹配，越具体/越长的词要排在它的子串词之前，
// 否则会被短词抢先命中（如「扁平插画」需排在「扁平」前，「新中式」需在「中式」前）。
const STYLE_KEYWORDS = [
  // 手绘 / 插画 / 漫画类
  ['扁平插画', '扁平插画'], ['扁平', '扁平风'], ['手绘', '手绘风'], ['水彩', '水彩风'],
  ['马克笔', '马克笔风'], ['蜡笔', '蜡笔风'], ['彩铅', '彩铅风'], ['插画', '插画风'],
  ['绘本', '绘本风'], ['漫画', '漫画风'], ['美漫', '美漫风'], ['日漫', '日漫风'],
  ['涂鸦', '涂鸦风'], ['线稿', '线稿风'], ['素描', '素描风'], ['速写', '速写风'],
  // 像素 / 低多边形 / 矢量
  ['像素', '像素风'], ['低多边形', '低多边形'], ['低面', '低多边形'], ['lowpoly', '低多边形'],
  ['等距', '等距 2.5D'], ['2.5d', '2.5D'], ['矢量', '矢量风'],
  // 潮流 / 氛围类
  ['赛博朋克', '赛博朋克'], ['蒸汽波', '蒸汽波'], ['故障艺术', '故障艺术'], ['glitch', '故障艺术'],
  ['霓虹', '霓虹风'], ['波普', '波普风'], ['孟菲斯', '孟菲斯风'], ['极简', '极简风'],
  ['极繁', '极繁风'], ['未来感', '未来感'], ['科技感', '科技感'], ['蓝图', '蓝图风'],
  ['blueprint', '蓝图风'], ['全息', '全息风'], ['酸性', '酸性设计'],
  // 国风 / 东方
  ['新中式', '新中式'], ['国潮', '国潮风'], ['中国风', '国风'], ['国风', '国风'],
  ['水墨', '水墨风'], ['工笔', '工笔画风'], ['敦煌', '敦煌风'], ['浮世绘', '浮世绘风'],
  ['ink', '水墨风'],
  // 质感 / 媒材类
  ['吉卜力', '吉卜力风'], ['新海诚', '新海诚风'], ['日系', '日系'], ['ins风', 'ins 风'],
  ['复古', '复古风'], ['胶片', '胶片质感'], ['拍立得', '拍立得风'], ['油画', '油画质感'],
  ['水粉', '水粉风'], ['黏土', '黏土风'], ['clay', '黏土风'], ['毛毡', '毛毡风'],
  ['折纸', '折纸风'], ['剪纸', '剪纸风'], ['手账', '手账风'],
  // 3D / 渲染
  ['c4d', 'C4D 渲染'], ['blender', '3D 渲染'], ['3D', '3D 渲染'], ['3d', '3D 渲染'],
  ['立体', '3D 渲染'], ['卡通', '卡通风'], ['皮克斯', '皮克斯风'], ['pixar', '皮克斯风'],
  // 写实 / 其它
  ['超写实', '超写实'], ['写实', '写实风'], ['超现实', '超现实'], ['梦幻', '梦幻风'],
  ['治愈', '治愈系'], ['黑白', '黑白'], ['极简线条', '极简线条'],
];

/** 从 prompt 文本提取画风短语，返回 [命中词, 展示标签]（找不到返回 [null, null]）。 */
function detectStyle(promptText) {
  if (!promptText) return [null, null];
  for (const [needle, label] of STYLE_KEYWORDS) {
    if (promptText.includes(needle)) return [needle, label];
  }
  return [null, null];
}

/**
 * 根据 prompt 推导标题：画风 + 主体，控制在 titleMaxLen 内。
 * 主体取 prompt 第一句的前若干字（去掉风格描述与标点）。
 */
function deriveTitle(promptText, maxLen) {
  if (!promptText) return null;
  const [, style] = detectStyle(promptText);
  // 取首句作为主体素材
  const firstSentence = promptText.split(/[。.!！?？\n,，;；]/)[0].trim();
  // 主体：去掉【所有】已知风格词（连同 风格/风/系 后缀）+ 指令性套话。
  // 一个 prompt 可能含多个风格词（如「治愈系插画风格」），只删匹配到的那个会留下
  // 另一个（导致「插画风的治愈系的猫」），所以这里把词表里出现的全部剔掉。
  let subject = firstSentence;
  for (const [needle] of STYLE_KEYWORDS) {
    if (subject.includes(needle)) {
      subject = subject.replace(new RegExp(`${needle}(风格|风|系)?`, 'g'), '');
    }
  }
  subject = subject
    .replace(/(一[张幅个]|画一[张幅个]?|生成|绘制|创作|帮我|请|画风|风格)/g, '')
    .replace(/的{2,}/g, '的')   // 折叠重复的「的」
    .replace(/^的+|的+$/g, '')
    .replace(/\s{2,}/g, ' ')   // 仅压缩多余空格，保留英文单词间的单空格
    .trim();

  let title;
  if (style) {
    title = subject ? `${style}的${subject}` : `${style}AI图`;
  } else {
    title = subject || 'AI 生成图片';
  }
  // 收口到长度上限（按 code point 计数，中文友好）
  const cps = [...title];
  if (cps.length > maxLen) title = cps.slice(0, maxLen).join('').trim();
  return title;
}

/**
 * 把 prompt 精简成可发布正文：取前 N 句、去掉技术性修饰词，控制在约 maxLen 字。
 * 目标是「读起来像人话的简介」，不是逐字照搬 prompt。
 */
function deriveContent(promptText, maxLen = 80) {
  if (!promptText) return null;
  // 去掉常见的技术/排版指令性描述，让正文更像自然语言。
  // 先吃掉「高清渲染 / 景深效果」这类整短语，避免只删半截留下「渲染，效果」。
  let text = promptText
    .replace(/\b(aspect[_ ]?ratio|16:9|4:3|1:1|9:16)\b/gi, '')
    .replace(/(超高清|高清|4k|8k|HDR)\s*(渲染|画质|画面)?[，,。.、]?/gi, '')
    .replace(/(景深|光影|渲染参数|分辨率)\s*(效果|质感)?[，,。.、]?/g, '')
    .replace(/\s*\n\s*/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();

  // 去掉开头的生图指令套话（「画一张手绘风格的…」→「…」），让正文不像 prompt
  text = text
    .replace(/^(帮我|请)?(画|生成|绘制|创作|做)(一[张幅个])?/u, '')
    .replace(/^[一-龥]{1,6}(风格|风)的?/u, '')   // 开头残留的「xx风格的」
    .replace(/^[，,、的\s]+/u, '')
    .trim();

  // 取前几句直到接近 maxLen
  const sentences = text.split(/(?<=[。.!！?？])/);
  let out = '';
  for (const s of sentences) {
    if ([...(out + s)].length > maxLen && out) break;
    out += s;
    if ([...out].length >= maxLen) break;
  }
  out = (out || text).trim();
  // 收尾清理：去掉结尾遗留的孤立标点/空句
  out = out.replace(/[，,、。.\s]+$/u, '');
  const cps = [...out];
  if (cps.length > maxLen) out = cps.slice(0, maxLen).join('').replace(/[，,、]$/u, '') + '…';
  return out;
}


/** 依次尝试一组候选 selector，返回第一个在 timeout 内可见的 locator（找不到返回 null）。 */
async function firstVisible(page, selectors, timeout) {
  const per = Math.max(1500, Math.floor(timeout / selectors.length));
  for (const sel of selectors) {
    try {
      const loc = page.locator(sel).first();
      await loc.waitFor({ state: 'visible', timeout: per });
      return loc;
    } catch {
      // 试下一个候选
    }
  }
  return null;
}

/** 检测是否已登录：任一 loggedIn 信号出现即为真。 */
async function isLoggedIn(page, timeout = 8000) {
  const loc = await firstVisible(page, SELECTORS.loggedIn, timeout);
  return loc !== null;
}

/**
 * 确保已登录。未登录则导航到登录页、提示扫码，轮询直到登录或超时。
 * 返回 true（已登录）/ false（超时未登录）。
 */
async function ensureLogin(page, timeout) {
  await page.goto(DEFAULTS.publishUrl, { waitUntil: 'domcontentloaded' }).catch(() => {});
  if (await isLoggedIn(page, 6000)) {
    log('✅ 已是登录态（复用持久化会话）');
    return true;
  }

  // 未登录 → 去登录页扫码
  log('🔐 未检测到登录态，打开登录页等待扫码…');
  await page.goto(DEFAULTS.loginUrl, { waitUntil: 'domcontentloaded' }).catch(() => {});
  const qr = await firstVisible(page, SELECTORS.qrcode, 8000);
  if (qr) {
    log('📱 请用小红书 App 扫描浏览器窗口中的二维码完成登录…');
  } else {
    log('📱 请在打开的浏览器窗口中完成登录（账号/二维码）…');
  }

  // 轮询登录态
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    await sleep(2500);
    if (await isLoggedIn(page, 3000)) {
      log('✅ 登录成功，会话已持久化，下次免扫码');
      return true;
    }
  }
  return false;
}

/**
 * 极简 PNG 解码（仅支持非隔行 RGBA/RGB/灰度，足够解析 Playwright 截图）。
 * 返回 { w, h, ch, data:Buffer(RGBA/...) }。用于在 closed shadow root 的发布栏里
 * 靠像素颜色定位「发布」红按钮（无法用 DOM selector）。
 */
function decodePNG(buf) {
  let p = 8; const idat = []; let w, h, ct;
  while (p < buf.length) {
    const len = buf.readUInt32BE(p);
    const type = buf.toString('ascii', p + 4, p + 8);
    const data = buf.slice(p + 8, p + 8 + len);
    if (type === 'IHDR') { w = data.readUInt32BE(0); h = data.readUInt32BE(4); ct = data[9]; }
    else if (type === 'IDAT') idat.push(data);
    else if (type === 'IEND') break;
    p += 12 + len;
  }
  const raw = inflateSync(Buffer.concat(idat));
  const ch = ct === 6 ? 4 : ct === 2 ? 3 : ct === 0 ? 1 : 4;
  const stride = w * ch;
  const out = Buffer.alloc(h * stride);
  const paeth = (a, b, c) => {
    const pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c);
    return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
  };
  let pos = 0;
  for (let y = 0; y < h; y++) {
    const ft = raw[pos++]; const line = raw.slice(pos, pos + stride); pos += stride;
    for (let x = 0; x < stride; x++) {
      const a = x >= ch ? out[y * stride + x - ch] : 0;
      const b = y > 0 ? out[(y - 1) * stride + x] : 0;
      const c = (x >= ch && y > 0) ? out[(y - 1) * stride + x - ch] : 0;
      let v = line[x];
      if (ft === 1) v += a; else if (ft === 2) v += b;
      else if (ft === 3) v += (a + b) >> 1; else if (ft === 4) v += paeth(a, b, c);
      out[y * stride + x] = v & 255;
    }
  }
  return { w, h, ch, data: out };
}

/**
 * 在「发布栏」截图里扫描小红书品牌红（≈255,36,66）像素，返回红块质心相对栏左上角的
 * { dx, dy }（找不到返回 null）。发布按钮并不在栏最右，而是偏中位置，颜色定位最稳。
 */
function findRedButtonOffset(png) {
  let sx = 0, sy = 0, cnt = 0;
  for (let y = 0; y < png.h; y++) {
    for (let x = 0; x < png.w; x++) {
      const i = (y * png.w + x) * png.ch;
      const r = png.data[i], g = png.data[i + 1], b = png.data[i + 2];
      if (r > 200 && g < 90 && b < 110 && (r - g) > 120) { sx += x; sy += y; cnt++; }
    }
  }
  if (cnt < 50) return null;
  return { dx: Math.round(sx / cnt), dy: Math.round(sy / cnt) };
}

/**
 * 切到「上传图文」tab。小红书改版后页面默认落在「上传视频」tab，且 DOM 里有多个
 * 同名 .creator-tab（部分是定位在屏外 x:-9726 的隐藏副本），内层 .title span 还会
 * 拦截指针事件。所以这里：① 只挑坐标为正（真正在屏内）的那个 tab；② 用 force 点击
 * 绕过 .title 拦截；③ 用「文件 input 的 accept 变成图片类型」作为成功判据，而不是
 * 看 .active class（.active 挂在屏外副本上，并不可靠）。
 * 成功返回 true。
 */
async function switchToImageTextTab(page, timeout) {
  const tabs = page.locator('.creator-tab', { hasText: '上传图文' });
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const n = await tabs.count().catch(() => 0);
    for (let i = 0; i < n; i++) {
      const t = tabs.nth(i);
      const box = await t.boundingBox().catch(() => null);
      if (!box || box.x < 0 || box.y < 0 || box.width <= 0) continue; // 跳过屏外副本
      // 先试常规点 .title，失败再 force 点父节点
      try { await t.locator('.title').click({ timeout: 3000 }); }
      catch {
        try { await t.click({ force: true, timeout: 3000 }); }
        catch { continue; }
      }
      await sleep(1500);
      // 成功判据：出现接受图片格式的 file input
      const ok = await page.evaluate(() =>
        [...document.querySelectorAll('input[type=file]')]
          .some((el) => /jpg|jpeg|png|webp/i.test(el.accept || ''))
      ).catch(() => false);
      if (ok) return true;
    }
    await sleep(1000);
  }
  return false;
}

/** 稳健点击：多候选 + 失败重试 1 次。成功返回 true。 */
async function clickFirst(page, selectors, timeout, label) {
  for (let attempt = 0; attempt < 2; attempt++) {
    const loc = await firstVisible(page, selectors, timeout);
    if (loc) {
      try {
        await loc.click({ timeout: 5000 });
        return true;
      } catch {
        if (attempt === 0) { await sleep(1000); continue; }
      }
    }
  }
  if (label) log(`⚠️  未能点击：${label}`);
  return false;
}

/**
 * 选「添加内容类型声明 = 笔记含AI合成内容」。AI 生成内容做合规声明更稳妥。
 * 该控件是 d-select 下拉，位于表单底部：点开下拉 → 选「笔记含AI合成内容」(注意是
 * 「合成」不是「生成」)。下拉项会渲染在控件下方，故需先把控件滚进视图(viewport 已
 * 调高到 1400 容纳展开区)。成功返回 true；失败返回 false（调用方仅警告，不阻断发布）。
 */
async function selectAIDeclaration(page, timeout) {
  // 1) 点开「添加内容类型声明」下拉
  const entry = await firstVisible(page, SELECTORS.declareEntry, 6000);
  if (!entry) return false;
  await entry.scrollIntoViewIfNeeded().catch(() => {});
  await sleep(600);
  await entry.click({ timeout: 5000 }).catch(() => {});
  await sleep(1800);

  // 2) 选「笔记含AI合成内容」（先试常规点，失败退回坐标点）
  let picked = false;
  for (const sel of SELECTORS.declareAIOption) {
    const opt = page.locator(sel).first();
    try {
      await opt.waitFor({ state: 'attached', timeout: 3000 });
      await opt.scrollIntoViewIfNeeded().catch(() => {});
      try {
        await opt.click({ timeout: 3500 });
        picked = true; break;
      } catch {
        const b = await opt.boundingBox().catch(() => null);
        if (b) { await page.mouse.click(b.x + b.width / 2, b.y + b.height / 2); picked = true; break; }
      }
    } catch { /* 试下一个候选 */ }
  }
  if (!picked) return false;
  await sleep(800);

  // 2.5) 关闭下拉浮层：选完若浮层不收起，会盖住发布按钮导致点击失效。
  //      用 Escape + 点回标题输入框（确定在表单内的安全元素）来收起浮层；
  //      切忌点屏幕左上角空白——那里是侧边栏导航，会误触跳走整个页面。
  await page.keyboard.press('Escape').catch(() => {});
  await sleep(400);
  const titleBox = await firstVisible(page, SELECTORS.titleInput, 3000);
  if (titleBox) { await titleBox.click().catch(() => {}); }
  await sleep(800);

  // 3) 校验声明栏已显示「笔记含AI合成内容」
  const ok = await page.evaluate(() =>
    [...document.querySelectorAll('div.d-select-main, div.d-select-wrapper, div.wrapper')]
      .some((e) => /笔记含AI合成内容/.test(e.innerText || ''))
  ).catch(() => false);
  return ok;
}

/**
 * 发布主流程：导航 → 进图文 tab → 上传图片 → 进编辑页 → 填三要素 → 停在发布按钮。
 * 传 cfg.publish 才真正点击发布。返回 { ok, stopped, published, message }。
 */
async function runPublish(page, cfg) {
  // 1) 进入发布页（已在 ensureLogin 里导航过，这里确保停在发布页）
  if (!page.url().includes('/publish/publish')) {
    await page.goto(DEFAULTS.publishUrl, { waitUntil: 'domcontentloaded' }).catch(() => {});
  }
  await sleep(1500);

  // 2) 切到「上传图文」tab（默认落在视频 tab；改版后需挑屏内 tab + force 点击）
  const switched = await switchToImageTextTab(page, 12000);
  if (!switched) {
    log('⚠️  未能确认切到「上传图文」tab，继续尝试定位图片上传入口…');
  }
  await sleep(1000);

  // 3) 上传图片：直接喂隐藏的 <input type=file>，避开系统文件框。
  //    隐藏 input 常带 opacity:0/display:none，firstVisible 可能判定为不可见，
  //    所以这里改用 attached 状态定位（setInputFiles 对隐藏 input 同样有效），
  //    并优先选 accept 含图片格式的 input。
  let uploadInput = null;
  for (const sel of SELECTORS.uploadInput) {
    const loc = page.locator(sel).first();
    try {
      await loc.waitFor({ state: 'attached', timeout: 4000 });
      uploadInput = loc;
      break;
    } catch { /* 试下一个候选 */ }
  }
  if (!uploadInput) {
    return { ok: false, message: '找不到图片上传入口（uploadInput selector 可能已失效，见脚本 SELECTORS）' };
  }
  try {
    await uploadInput.setInputFiles(cfg.images.map((p) => resolve(p)));
    log(`📤 已提交 ${cfg.images.length} 张图片上传`);
  } catch (e) {
    return { ok: false, message: `图片上传失败: ${e.message}` };
  }

  // 4) 等编辑页就绪（标题框出现即视为进入编辑页）
  const titleBox = await firstVisible(page, SELECTORS.titleInput, cfg.timeout);
  if (!titleBox) {
    return { ok: false, message: '上传后未进入编辑页（标题框未出现，可能图片仍在上传或 selector 失效）' };
  }

  // 5) 填标题
  try {
    await titleBox.click();
    await titleBox.fill('');
    await titleBox.type(cfg.title, { delay: 20 });
    log(`📝 标题已填：「${cfg.title}」(${[...cfg.title].length} 字)`);
  } catch (e) {
    return { ok: false, message: `填写标题失败: ${e.message}` };
  }

  // 6) 填正文（contenteditable，需聚焦后输入触发事件）
  const editor = await firstVisible(page, SELECTORS.contentEditor, cfg.timeout);
  if (!editor) {
    return { ok: false, message: '找不到正文编辑区（contentEditor selector 可能已失效）' };
  }
  try {
    await editor.click();
    await editor.type(cfg.content, { delay: 8 });
    log(`📝 正文已填（${[...cfg.content].length} 字）`);
  } catch (e) {
    return { ok: false, message: `填写正文失败: ${e.message}` };
  }

  // 7) 话题：正文末尾逐个输入 #话题，并选中下拉项（避免纯文本丢 topic entity）
  if (cfg.topics.length) {
    for (const topic of cfg.topics) {
      try {
        await editor.click();
        await page.keyboard.press('End');
        await editor.type(` #${topic}`, { delay: 30 });
        await sleep(1200); // 等下拉弹出
        const opt = await firstVisible(page, SELECTORS.topicOption, 3000);
        if (opt) {
          await opt.click().catch(() => {});
        } else {
          // 下拉没弹出就敲空格收尾，至少保留文本话题
          await editor.type(' ', { delay: 20 });
        }
      } catch {
        // 单个话题失败不阻断后续
      }
    }
    log(`🏷️  已尝试添加话题：${cfg.topics.map((t) => '#' + t).join(' ')}`);
  }

  await sleep(1000);

  // 7.5) 选「内容类型声明 = 笔记含AI合成内容」（默认开启；--no-ai-declare 关闭）。
  //      AI 生成内容做合规声明更稳妥；失败仅警告，不阻断发布。
  if (cfg.aiDeclare) {
    try {
      const ok = await selectAIDeclaration(page, cfg.timeout);
      if (ok) log('✅ 已选内容类型声明：笔记含AI合成内容');
      else log('⚠️  未能选「笔记含AI合成内容」声明（selector 可能已变），将不带声明继续');
    } catch (e) {
      log(`⚠️  选AI声明异常：${e.message}，将不带声明继续`);
    }
    await sleep(800);
  }

  // 8) 定位发布按钮。改版后首选 <xhs-publish-btn>（sticky，常在折叠下方），
  //    需先 scrollIntoView；它可能不被判定为 visible，故用 attached 状态定位。
  let publishBtn = null;
  let publishIsCustomEl = false;
  for (const sel of SELECTORS.publishButton) {
    const loc = page.locator(sel).first();
    try {
      await loc.waitFor({ state: 'attached', timeout: 4000 });
      await loc.scrollIntoViewIfNeeded().catch(() => {});
      publishBtn = loc;
      publishIsCustomEl = sel === 'xhs-publish-btn';
      break;
    } catch { /* 试下一个候选 */ }
  }
  if (!publishBtn) {
    return { ok: false, message: '找不到发布按钮（publishButton selector 可能已失效）' };
  }
  // 自定义元素若标了 submit-disabled，提示但不强行阻断（人工可在浏览器确认）
  if (publishIsCustomEl) {
    const disabled = await publishBtn.getAttribute('submit-disabled').catch(() => null);
    if (disabled === 'true') {
      log('⚠️  发布按钮当前为禁用态（submit-disabled=true），可能内容仍在校验/上传');
    }
  }

  // 9) 截图（无论停手还是发布，先留证据）
  const shotPath = cfg.screenshot
    || join(tmpdir(), `xhs-publish-${new Date().toISOString().replace(/[:.]/g, '-')}.png`);
  await page.screenshot({ path: shotPath, fullPage: true }).catch(() => {});

  if (!cfg.publish) {
    // 默认安全行为：停在发布按钮，等人工确认
    return {
      ok: true, stopped: true, published: false, screenshot: shotPath,
      message: '已到发布页并填好内容，停在「发布」按钮。请在浏览器中人工确认后点击发布。',
    };
  }

  // 10) 显式 --publish 才真正发布
  try {
    if (publishIsCustomEl) {
      // <xhs-publish-btn> 是 closed shadow root，内部「发布」按钮 selector 拿不到，
      // 且发布按钮并不在栏最右（偏中位置）。策略：截发布栏图 → 扫描品牌红像素定位
      // 「发布」按钮质心 → 坐标点击；扫不到红块时退回 host 偏中略偏左的经验坐标。
      const box = await publishBtn.boundingBox();
      if (!box) throw new Error('无法获取发布按钮位置');
      const barShot = join(tmpdir(), `xhs-pubbar-${Date.now()}.png`);
      let clickX = box.x + box.width * 0.6, clickY = box.y + box.height / 2;
      try {
        await publishBtn.screenshot({ path: barShot });
        const off = findRedButtonOffset(decodePNG(await readFile(barShot)));
        if (off) { clickX = box.x + off.dx; clickY = box.y + off.dy; }
        else log('⚠️  未扫描到红色发布按钮，退回经验坐标点击');
      } catch {
        log('⚠️  发布栏取色失败，退回经验坐标点击');
      } finally {
        await unlink(barShot).catch(() => {});
      }
      await page.mouse.click(clickX, clickY);
    } else {
      await publishBtn.click({ timeout: 8000 });
    }
  } catch (e) {
    return { ok: false, screenshot: shotPath, message: `点击发布失败: ${e.message}（请人工点击）` };
  }
  // 成功判据：跳转到 /publish/success（最可靠），或出现「发布成功」文案。
  let published = false;
  try {
    await page.waitForURL(/\/publish\/success/, { timeout: 15000 });
    published = true;
  } catch { /* 没跳转就退回看文案 */ }
  if (!published) {
    const success = await firstVisible(page, SELECTORS.publishSuccess, 5000);
    if (success) published = true;
  }
  if (published) {
    return { ok: true, published: true, screenshot: shotPath, message: '发布成功 🎉' };
  }
  return {
    ok: true, published: false, screenshot: shotPath,
    message: '已点击发布，但未捕获到成功提示。请在浏览器/创作后台确认是否发布成功。',
  };
}

// ─── Validation ─────────────────────────────────────────────────────────────

/** 校验参数；返回错误信息数组（空数组=通过）。
 * 同时：读 --content-file / --prompt-file，并在缺省时从 prompt 推导标题/正文。
 * 推导来源标记写入 cfg.titleSource / cfg.contentSource（用于输出提示）。
 */
async function validate(cfg) {
  const errors = [];

  // 图片来源：--image（已有图）或 --prompt/--prompt-file（先生成）。
  // 有 --image 时校验存在；没有 --image 但有生图来源时，留到 main() 里生成。
  cfg.willGenerate = false;
  if (cfg.images.length) {
    for (const img of cfg.images) {
      if (!(await fileExists(resolve(img)))) {
        errors.push(`图片不存在: ${img}`);
      }
    }
  } else if (cfg.prompt || cfg.promptFile) {
    cfg.willGenerate = true; // 稍后用 prompt 生图
  } else {
    errors.push('缺少图片：请用 --image 指定已有图，或用 --prompt/--prompt-file 让脚本先生成');
  }

  // prompt 文本来源（供生图 + 标题/正文推导）：--prompt 优先，否则读 --prompt-file
  let promptText = cfg.prompt || null;
  if (!promptText && cfg.promptFile) {
    if (!(await fileExists(resolve(cfg.promptFile)))) {
      errors.push(`prompt 文件不存在: ${cfg.promptFile}`);
    } else {
      promptText = await readPromptFile(cfg.promptFile);
      if (!promptText) errors.push(`无法从 prompt 文件解析内容: ${cfg.promptFile}`);
    }
  }
  cfg.promptText = promptText; // 存起来给 main() 生图用

  // 正文：--content > --content-file > 由 prompt 精简推导
  cfg.contentSource = 'arg';
  if (!cfg.content && cfg.contentFile) {
    if (!(await fileExists(resolve(cfg.contentFile)))) {
      errors.push(`正文文件不存在: ${cfg.contentFile}`);
    } else {
      try {
        cfg.content = (await readFile(resolve(cfg.contentFile), 'utf8')).trim();
        cfg.contentSource = 'file';
      } catch (e) {
        errors.push(`读取正文文件失败: ${e.message}`);
      }
    }
  }
  if (!cfg.content && promptText) {
    cfg.content = deriveContent(promptText, 80);
    cfg.contentSource = 'prompt';
  }
  if (!cfg.content) {
    errors.push('缺少正文：请用 --content / --content-file 指定，或用 --prompt/--prompt-file 自动精简');
  }

  // 标题：--title > 由 prompt 按画风推导
  cfg.titleSource = 'arg';
  if (!cfg.title && promptText) {
    cfg.title = deriveTitle(promptText, DEFAULTS.titleMaxLen);
    cfg.titleSource = 'prompt';
  }
  if (!cfg.title) {
    errors.push('缺少标题：请用 --title 指定，或用 --prompt/--prompt-file 按图片风格自动生成');
  } else if ([...cfg.title].length > DEFAULTS.titleMaxLen) {
    // 推导出的标题已收口到上限；这里主要拦显式 --title 超长
    errors.push(`标题超长：${[...cfg.title].length} 字 > ${DEFAULTS.titleMaxLen} 字上限，请压缩后重试`);
  }

  return errors;
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const cfg = parseArgs();

  if (cfg.help) {
    printHelp();
    process.exit(0);
  }

  console.log('='.repeat(50));
  console.log('📕 小红书图文笔记发布');
  console.log('='.repeat(50));

  const errors = await validate(cfg);
  if (errors.length) {
    console.error('\n❌ 参数校验未通过：');
    for (const e of errors) console.error(`   - ${e}`);
    printHelp();
    process.exit(1);
  }

  // dry-run：只打印将执行的步骤与参数，不启动浏览器
  if (cfg.dryRun) {
    const tSrc = { arg: '(--title)', prompt: '(按图片风格自动生成)' }[cfg.titleSource] || '';
    const cSrc = { arg: '(--content)', file: '(--content-file)', prompt: '(prompt 精简)' }[cfg.contentSource] || '';
    console.log('\n🔍 DRY-RUN（不启动浏览器）');
    if (cfg.willGenerate) {
      const count = Math.max(1, cfg.count || 1);
      console.log(`   图片: 待生成 ${count} 张（provider=${cfg.provider}, ar=${cfg.aspectRatio}）`);
      console.log(`   生图 prompt: ${cfg.promptText.slice(0, 60).replace(/\n/g, ' ')}${cfg.promptText.length > 60 ? '…' : ''}`);
    } else {
      console.log(`   图片(${cfg.images.length}): ${cfg.images.join(', ')}`);
    }
    console.log(`   标题: 「${cfg.title}」(${[...cfg.title].length} 字) ${tSrc}`);
    const preview = cfg.content.length > 80 ? cfg.content.slice(0, 80) + '…' : cfg.content;
    console.log(`   正文: ${preview.replace(/\n/g, ' ')} (${[...cfg.content].length} 字) ${cSrc}`);
    console.log(`   话题: ${cfg.topics.length ? cfg.topics.map((t) => '#' + t).join(' ') : '(无)'}`);
    console.log(`   内容声明: ${cfg.aiDeclare ? '笔记含AI合成内容' : '不声明（--no-ai-declare）'}`);
    console.log(`   发布行为: ${cfg.publish ? '自动点击发布' : '停在发布按钮（默认，需人工确认）'}`);
    console.log(`   登录态目录: ${cfg.userDataDir}`);
    console.log('\n将执行步骤：'
      + (cfg.willGenerate ? `生成 ${Math.max(1, cfg.count || 1)} 张图片 → ` : '')
      + '登录校验 → 进图文 tab → 上传图片 → 填标题/正文/话题 → '
      + (cfg.aiDeclare ? '选AI合成声明 → ' : '')
      + (cfg.publish ? '点击发布' : '停在发布按钮并截图'));
    process.exit(0);
  }

  // 生成即发布：没有 --image 但有 prompt → 先生图
  if (cfg.willGenerate) {
    const output = cfg.output || join(
      tmpdir(),
      `xhs-image-${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
    );
    const count = Math.max(1, cfg.count || 1);
    const gen = await generateImages(cfg.promptText, output, count, cfg.aspectRatio, cfg.provider);
    if (!gen.ok) {
      console.error(`\n❌ ${gen.message}`);
      process.exit(1);
    }
    cfg.images = gen.paths;
    const totalKB = (await Promise.all(gen.paths.map(p => stat(p).then(s => s.size)))).reduce((a, b) => a + b, 0) / 1024;
    console.log(`✅ 已生成 ${gen.paths.length} 张图片 (共 ${Math.round(totalKB)} KB)`);
    gen.paths.forEach(p => console.log(`   - ${p}`));
  }

  // 检测 Playwright Chromium 内核是否已安装
  await mkdir(cfg.userDataDir, { recursive: true }).catch(() => {});

  // 懒加载 playwright：dry-run/help/校验都不需要它，缺包时也能用
  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch {
    console.error('\n❌ 未安装 playwright。请在技能目录执行：');
    console.error('     npm install            # 安装 playwright 依赖');
    console.error('     npm run setup:xhs      # 安装 Chromium 内核（playwright install chromium）');
    process.exit(1);
  }

  // 首次未登录时需要 headed 才能扫码 → 这里先用 headed 探测一次更稳妥；
  // 若用户显式 --headed 也尊重。无头模式下无法扫码，因此默认 headed=false 时
  // 仍会在检测到未登录后由浏览器窗口完成（持久化目录已有登录态则无头亦可）。
  // 停手模式（没加 --publish）本质是要人工在窗口里确认并点发布，必须可见窗口，
  // 否则无头跑完即退、用户什么也看不到 → 这里强制 headed。
  const headless = cfg.publish ? !cfg.headed : false;

  let context;
  try {
    context = await chromium.launchPersistentContext(cfg.userDataDir, {
      headless,
      viewport: { width: 1280, height: 900 },
      args: ['--disable-blink-features=AutomationControlled'],
    });
  } catch (e) {
    console.error(`\n❌ 启动 Chromium 失败: ${e.message}`);
    console.error('   可能未安装内核，请先执行： npx playwright install chromium');
    console.error('   或在技能目录执行： npm run setup:xhs');
    process.exit(1);
  }

  const page = context.pages()[0] || (await context.newPage());
  page.setDefaultTimeout(cfg.timeout);

  let exitCode = 0;
  try {
    // 登录校验
    let loggedIn = await ensureLogin(page, DEFAULTS.loginTimeout);

    // 无头模式下未登录无法扫码：重启为 headed 再试一次
    if (!loggedIn && headless) {
      console.log('\n⚠️  无头模式无法扫码登录，正在切换为可见窗口重试…');
      await context.close().catch(() => {});
      context = await chromium.launchPersistentContext(cfg.userDataDir, {
        headless: false,
        viewport: { width: 1280, height: 900 },
        args: ['--disable-blink-features=AutomationControlled'],
      });
      const p2 = context.pages()[0] || (await context.newPage());
      p2.setDefaultTimeout(cfg.timeout);
      loggedIn = await ensureLogin(p2, DEFAULTS.loginTimeout);
      if (loggedIn) {
        const result = await runPublish(p2, cfg);
        exitCode = reportResult(result);
        await context.close().catch(() => {});
        process.exit(exitCode);
      }
    }

    if (!loggedIn) {
      console.error('\n❌ 登录超时（未在规定时间内完成扫码）。请重试，或用 --headed 手动登录一次。');
      await context.close().catch(() => {});
      process.exit(1);
    }

    const result = await runPublish(page, cfg);
    exitCode = reportResult(result);
  } catch (e) {
    console.error(`\n❌ 执行出错: ${e.message}`);
    exitCode = 1;
  } finally {
    // 发布完成（--publish）直接关；停手模式要把窗口留给用户人工确认/点发布，
    // 不能 1.5 秒就强关（窗口一闪而过，根本来不及操作）。改为等浏览器被用户
    // 手动关闭（监听 context.close 事件），并打印提示。
    if (cfg.publish) {
      await sleep(500);
      await context.close().catch(() => {});
    } else {
      console.log('\n🪟 浏览器窗口保持打开，请在窗口中确认内容并手动点击「发布」。');
      console.log('   完成后直接关闭浏览器窗口即可（脚本会随之退出）。');
      await new Promise((res) => {
        context.on('close', res);
        // 兜底：所有页面都被关掉也视为用户结束
        page.on('close', () => context.close().catch(() => {}).finally(res));
      });
    }
  }
  process.exit(exitCode);
}

/** 统一结果输出，返回退出码。 */
function reportResult(result) {
  console.log('\n' + '─'.repeat(50));
  if (!result.ok) {
    console.error(`❌ 失败: ${result.message}`);
    if (result.screenshot) console.log(`📸 截图: ${result.screenshot}`);
    return 1;
  }
  if (result.stopped) {
    console.log(`🛑 ${result.message}`);
    console.log(`📸 已截图: ${result.screenshot}`);
    console.log('💡 确认无误后，在浏览器窗口中点击「发布」，或重跑命令并加 --publish 自动发布。');
  } else if (result.published) {
    console.log(`✅ ${result.message}`);
    if (result.screenshot) console.log(`📸 截图: ${result.screenshot}`);
  } else {
    console.log(`⚠️  ${result.message}`);
    if (result.screenshot) console.log(`📸 截图: ${result.screenshot}`);
  }
  return 0;
}

main().catch((e) => {
  console.error(`\n❌ 未捕获错误: ${e.message}`);
  process.exit(1);
});




