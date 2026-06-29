#!/usr/bin/env node

/**
 * Publish an image-text post (图文) to Douyin (抖音) creator platform
 * via a persistent Playwright Chromium session.
 *
 * Design goals (mirrors publish_xiaohongshu.js):
 *  - Self-contained: just Playwright Chromium, no MCP/daemon needed.
 *  - Persistent login: first run scans a QR code, later runs reuse the session.
 *  - Safe by default: fill everything, then STOP at the publish button and
 *    screenshot. Only --publish actually clicks publish.
 *  - Generate-and-publish: pass --prompt with no --image to generate first.
 *
 * Flow: creator.douyin.com → 上传页 → 发布图文 tab → 上传图文 → 标题/简介 → 发布,
 * on a Playwright persistent context (login persists across runs).
 *
 * Usage:
 *   node scripts/publish_douyin.js \
 *     --image cover.png --title "标题" --content "正文简介" --topics "AI,效率"
 *
 *   # generate-and-publish (no --image):
 *   node scripts/publish_douyin.js --prompt "赛博朋克风格的城市夜景"
 *
 *   # preview only (no browser):
 *   node scripts/publish_douyin.js --image x.png --title x --content y --dry-run
 */

// NOTE: playwright is imported lazily inside main() (dynamic import) so that
// --dry-run / --help / arg-validation work even before the package is installed.
import { readFile, writeFile, mkdir, access, readdir, stat, copyFile, unlink } from 'node:fs/promises';
import { resolve, join, dirname } from 'node:path';
import { homedir, tmpdir } from 'node:os';
import { spawn } from 'node:child_process';

// ─── Config ─────────────────────────────────────────────────────────────────

const DEFAULTS = {
  homeUrl: 'https://creator.douyin.com/',
  uploadUrl: 'https://creator.douyin.com/creator-micro/content/upload',
  userDataDir: join(homedir(), '.image-factory-skill', 'douyin-profile'),
  stepTimeout: 30000,          // per-step timeout (ms)
  loginTimeout: 180000,        // wait up to 3 min for QR scan
  titleMaxLen: 30,             // 抖音「作品标题」上限约 30 字
  genTimeoutMs: 5 * 60 * 1000, // image generation timeout (5 min)
};

// 同目录下的生图脚本 + codex 兜底目录（与 send_feishu_image.py 对齐）
const SCRIPT_DIR = dirname(new URL(import.meta.url).pathname);
const SKILL_DIR = dirname(SCRIPT_DIR);
const PROMPTS_DIR = join(SKILL_DIR, 'prompts');
const GENERATE_IMAGE_JS = join(SCRIPT_DIR, 'generate-image.js');
const CODEX_GENERATED_DIR = join(homedir(), '.codex', 'generated_images');

// ─── Selectors (MAINTENANCE POINT) ──────────────────────────────────────────
// 抖音创作者平台会改版。某一步失效时，先来这里更新。每个键是「候选 selector 列表」，
// 按顺序尝试，取第一个命中的（has-text/属性选择器，适配 Playwright）。

const SELECTORS = {
  // 已登录信号：只认「高清发布」按钮——它仅在登录后出现。
  // 注意：不要用 [class*="avatar"]，登出态的营销落地页也有 avatar 元素（实测会误判已登录）。
  loggedIn: [
    'button[class*="douyin-creator-master-button"]',
    '#douyin-creator-master-side-upload-wrap button',
  ],
  // 登录入口（登出态落地页上的「登录」按钮，点击后弹出二维码）
  loginEntry: [
    'button:has-text("登录")',
    'div[class*="login"]:has-text("登录")',
    'span:has-text("登录")',
  ],
  // 登录页二维码（抖音用 aria-label="二维码"）
  qrcode: [
    'img[aria-label="二维码"]',
    'img[class*="qrcode"]',
    'img[src*="qrcode"]',
  ],
  // 左上角「高清发布」按钮 — 点击进入上传页
  hdPublishBtn: [
    'button[class*="douyin-creator-master-button"]',
    '#douyin-creator-master-side-upload-wrap button',
    'button.header-button-KP2xn1',
  ],
  // 发布类型 tab：发布图文
  tabImageText: [
    'div[class*="tab-item"]:has-text("发布图文")',
  ],
  // 「上传图文」按钮（发布图文 tab 下）
  uploadImageTextBtn: [
    'div[class*="drag-upload"] button:has-text("上传图文")',
    'button[class*="container-drag-btn"]:has-text("上传图文")',
  ],
  // 图片上传 file input（隐藏，setInputFiles 直接喂）
  uploadFileInput: [
    'div[class*="drag-upload"] input[type="file"]',
    'input[type="file"][accept*="image"]',
    'input[type="file"]',
  ],
  // 标题输入框（标准 input）
  titleInput: [
    'input[placeholder*="作品标题"]',
    'input.semi-input-default[placeholder*="标题"]',
    'input[placeholder*="标题"]',
  ],
  // 作品简介（slate 富文本 contenteditable div）
  descriptionInput: [
    'div[data-placeholder*="作品简介"][contenteditable="true"]',
    'div.editor-kit-container[contenteditable="true"]',
    'div[contenteditable="true"][data-slate-editor="true"]',
  ],
  // 「选择音乐」入口（编辑页右侧按钮）
  musicEntry: [
    'div[class*="container-right"]:has-text("选择音乐")',
    'div[class*="title"]:has-text("选择音乐")',
    'text=选择音乐',
  ],
  // 音乐面板「推荐」tab（确保停在推荐列表）
  musicRecommendTab: [
    'div[class*="semi-tabs-tab"]:has-text("推荐")',
  ],
  // 推荐列表里的歌曲项（hover 后浮现「使用」按钮）
  musicSongItem: [
    'div[class*="song-info"]',
    'div[class*="song-item"]',
  ],
  // 歌曲项 hover 后的「使用」按钮
  musicUseBtn: [
    'button[class*="apply-btn"]',
    'button.semi-button-primary:has-text("使用")',
  ],
  // 「自主声明」入口（编辑页设置区，点开弹「请选择声明类型」模态框）
  declareEntry: [
    'div[class*="controlWrapper"]:has-text("请选择自主声明")',
    'div[class*="selectText"]:has-text("请选择自主声明")',
    'text=请选择自主声明',
  ],
  // 声明弹窗里「内容由AI生成」单选项
  declareAIOption: [
    'label:has-text("内容由AI生成")',
    'span.semi-radio-addon:has-text("内容由AI生成")',
    'text=内容由AI生成',
  ],
  // 声明弹窗「确定」按钮（选中某项后才从 disabled 变可点）
  declareConfirmBtn: [
    'button:has-text("确定")',
  ],
  // 发布按钮所在卡片容器（发布按钮文本严格等于「发布」，在容器里用文本筛）
  publishContainer: [
    'div[class*="card-container-creator-layout"]',
  ],
  // 发布成功 toast
  publishToast: [
    'span[class*="semi-toast-content-text"]',
  ],
};

// ─── Argument parsing ───────────────────────────────────────────────────────
// 手写解析，风格对齐 generate-image.js / publish_xiaohongshu.js（不引额外依赖）。

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    images: [],
    prompt: null,           // 直接给文字 prompt，先生图再发布
    provider: 'auto',       // 生图后端 auto|codex|gemini
    aspectRatio: '3:4',     // 生图宽高比（抖音图文竖图友好，默认 3:4）
    output: null,           // 生成图片保存路径（缺省用临时文件）
    title: null,
    content: null,
    contentFile: null,
    promptFile: null,       // 自动推导 title/content（也可作生图来源）
    topics: [],             // 话题，作为 #tag 追加到简介末尾
    music: true,            // 默认自动选「推荐」第一首配乐；--no-music 关闭
    aiDeclare: true,        // 默认勾选「自主声明=内容由AI生成」(AI内容不声明会违规)；--no-ai-declare 关闭
    publish: false,
    headed: false,
    userDataDir: process.env.DOUYIN_USER_DATA_DIR || DEFAULTS.userDataDir,
    screenshot: null,
    timeout: DEFAULTS.stepTimeout,
    dryRun: false,
    help: false,
  };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    switch (a) {
      case '--image': case '-i':
        cfg.images.push(...args[++i].split(',').map((s) => s.trim()).filter(Boolean));
        break;
      case '--prompt': case '-P': cfg.prompt = args[++i]; break;
      case '--provider': cfg.provider = args[++i]; break;
      case '--aspect-ratio': case '--ar': cfg.aspectRatio = args[++i]; break;
      case '--output': case '-o': cfg.output = args[++i]; break;
      case '--title': case '-t': cfg.title = args[++i]; break;
      case '--content': case '-c': cfg.content = args[++i]; break;
      case '--content-file': cfg.contentFile = args[++i]; break;
      case '--prompt-file': cfg.promptFile = args[++i]; break;
      case '--topics':
        cfg.topics.push(...args[++i].split(',').map((s) => s.trim().replace(/^#/, '')).filter(Boolean));
        break;
      case '--publish': cfg.publish = true; break;
      case '--no-music': cfg.music = false; break;
      case '--no-ai-declare': cfg.aiDeclare = false; break;
      case '--headed': cfg.headed = true; break;
      case '--user-data-dir': cfg.userDataDir = args[++i]; break;
      case '--screenshot': cfg.screenshot = args[++i]; break;
      case '--timeout': cfg.timeout = parseInt(args[++i], 10) || DEFAULTS.stepTimeout; break;
      case '--dry-run': cfg.dryRun = true; break;
      case '--help': case '-h': cfg.help = true; break;
      default:
        if (a.startsWith('-')) console.error(`⚠️  未知参数: ${a}`);
    }
  }
  return cfg;
}

function printHelp() {
  console.log(`
抖音图文发布（Playwright）

用法:
  # A. 发已有图
  node scripts/publish_douyin.js --image <图> [--title <标题>] [--content <简介>] [选项]
  # B. 生成即发布（无 --image，先生图再发）
  node scripts/publish_douyin.js --prompt "<生图描述>" [--title ...] [选项]

图片来源（二选一）:
  --image, -i <路径>       已有图，逗号分隔或多次传入（首图=封面）
  --prompt, -P <文本>      生图描述：无 --image 时先调 generate-image.js 生成再发布
  --prompt-file <路径>     prompt 文件（prompts/YYYYMMDD-NN.md）：可作生图来源，
                           也用于在缺 --title/--content 时自动推导

生图选项（仅在用 --prompt/--prompt-file 生成时有效）:
  --provider <auto|codex|gemini>  生图后端（默认 auto）
  --aspect-ratio, --ar <W:H>      宽高比（默认 3:4，抖音竖图友好）
  --output, -o <路径>             生成图保存路径（默认临时文件）

标题与简介（缺省可由 prompt 自动推导）:
  --title, -t <文本>       作品标题（<=${DEFAULTS.titleMaxLen} 字，强校验）；缺省时按图片风格自动生成
  --content, -c <文本>     作品简介正文
  --content-file <路径>    从文件读简介

可选:
  --topics <a,b,c>         话题，逗号分隔（不带 #，脚本自动加），追加到简介末尾
  --no-music               不自动配乐（默认会自动选「推荐」第一首配乐）
  --no-ai-declare          不勾选AI生成声明（默认勾选「内容由AI生成」，AI内容不声明有违规风险）
  --publish                自动点击发布（默认仅停在发布按钮，等人工确认）
  --headed                 显示浏览器窗口（首次登录/调试；未登录时自动开启）
  --user-data-dir <目录>   持久化登录态目录（默认 ~/.image-factory-skill/douyin-profile）
  --screenshot <路径>      停手时截图保存路径（默认 /tmp/douyin-publish-<ts>.png）
  --timeout <毫秒>         单步超时（默认 ${DEFAULTS.stepTimeout}）
  --dry-run                预览参数与步骤，不启动浏览器/不生图
  --help, -h               显示帮助

环境变量:
  DOUYIN_USER_DATA_DIR     等价于 --user-data-dir

一条龙：--prompt 生图 → 自动归档 prompt → 自动推导标题/简介 → 发布（默认停在发布按钮）。
安全：默认填好内容后停在「发布」按钮并截图，由你人工确认后点击发布。
首次运行会弹窗扫码登录（抖音 App 扫码），登录态持久化后免扫码。
`);
}

// ─── Helpers ────────────────────────────────────────────────────────────────

const log = (msg) => console.log(msg);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function fileExists(p) {
  try { await access(p); return true; } catch { return false; }
}

// ─── Prompt → title/content derivation ──────────────────────────────────────
// 与 generate-image.js / send_feishu_image.py 解析一致：优先取 PROMPT: 段，
// 否则剥离 --- frontmatter 后取全文。返回纯 prompt 文本（失败返回 null）。
async function readPromptFile(path) {
  let content;
  try {
    content = await readFile(resolve(path), 'utf8');
  } catch {
    return null;
  }
  const m = content.match(/^PROMPT:\s*\n([\s\S]+?)(?=\n---|\n##\s|$)/m);
  if (m) return m[1].trim();

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
    return newest.path;
  }
}

/** 把 prompt 归档到 prompts/YYYYMMDD-NN.md（与 send_feishu_image.py 命名一致）。 */
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
  const sinceTs = Date.now() - 5000;
  const promptFile = join(tmpdir(), `douyin-genprompt-${Date.now()}.md`);
  try {
    await writeFile(promptFile, `---\naspect_ratio: "${aspectRatio}"\n---\n\nPROMPT:\n${promptText}\n`, 'utf8');
    log(`🎨 生成图片中…（provider=${provider}, ar=${aspectRatio}）`);
    const { code, stdout, stderr } = await execCommand('node', [
      GENERATE_IMAGE_JS, '--prompt-file', promptFile, '--output', output,
      '--aspect-ratio', aspectRatio, '--provider', provider,
    ], DEFAULTS.genTimeoutMs);

    if (code === 0 && (await fileExists(output)) && (await stat(output)).size > 0) {
      const archived = await archivePrompt(promptText, aspectRatio, provider);
      if (archived) log(`📝 Prompt 已归档: ${archived.split('/').pop()}`);
      return { ok: true, path: output };
    }
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

// 风格词库：从 prompt 里识别画风，用于生成标题。顺序≈优先级。
// detectStyle 用 includes 匹配，越具体/越长的词要排在它的子串词之前。
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

/** 根据 prompt 推导标题：画风 + 主体，控制在 maxLen 内。 */
function deriveTitle(promptText, maxLen) {
  if (!promptText) return null;
  const [, style] = detectStyle(promptText);
  const firstSentence = promptText.split(/[。.!！?？\n,，;；]/)[0].trim();
  // 去掉【所有】已知风格词（连同 风格/风/系 后缀）+ 指令性套话
  let subject = firstSentence;
  for (const [needle] of STYLE_KEYWORDS) {
    if (subject.includes(needle)) {
      subject = subject.replace(new RegExp(`${needle}(风格|风|系)?`, 'g'), '');
    }
  }
  subject = subject
    .replace(/(一[张幅个]|画一[张幅个]?|生成|绘制|创作|帮我|请|画风|风格)/g, '')
    .replace(/的{2,}/g, '的')
    .replace(/^的+|的+$/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim();

  let title;
  if (style) {
    title = subject ? `${style}的${subject}` : `${style}AI图`;
  } else {
    title = subject || 'AI 生成图片';
  }
  const cps = [...title];
  if (cps.length > maxLen) title = cps.slice(0, maxLen).join('').trim();
  return title;
}

/** 把 prompt 精简成可发布正文：去技术性修饰词 + 指令套话，截到约 maxLen 字。 */
function deriveContent(promptText, maxLen = 100) {
  if (!promptText) return null;
  let text = promptText
    .replace(/\b(aspect[_ ]?ratio|16:9|4:3|1:1|9:16)\b/gi, '')
    .replace(/(超高清|高清|4k|8k|HDR)\s*(渲染|画质|画面)?[，,。.、]?/gi, '')
    .replace(/(景深|光影|渲染参数|分辨率)\s*(效果|质感)?[，,。.、]?/g, '')
    .replace(/\s*\n\s*/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();

  text = text
    .replace(/^(帮我|请)?(画|生成|绘制|创作|做)(一[张幅个])?/u, '')
    .replace(/^[一-龥]{1,6}(风格|风)的?/u, '')
    .replace(/^[，,、的\s]+/u, '')
    .trim();

  const sentences = text.split(/(?<=[。.!！?？])/);
  let out = '';
  for (const s of sentences) {
    if ([...(out + s)].length > maxLen && out) break;
    out += s;
    if ([...out].length >= maxLen) break;
  }
  out = (out || text).trim();
  out = out.replace(/[，,、。.\s]+$/u, '');
  const cps = [...out];
  if (cps.length > maxLen) out = cps.slice(0, maxLen).join('').replace(/[，,、]$/u, '') + '…';
  return out;
}

// PLACEHOLDER_DOM

// ─── DOM helpers ─────────────────────────────────────────────────────────────

/** 依次尝试一组候选 selector，返回第一个在 timeout 内可见的 locator（找不到返回 null）。 */
async function firstVisible(page, selectors, timeout) {
  const per = Math.max(1500, Math.floor(timeout / selectors.length));
  for (const sel of selectors) {
    try {
      const loc = page.locator(sel).first();
      await loc.waitFor({ state: 'visible', timeout: per });
      return loc;
    } catch { /* 试下一个候选 */ }
  }
  return null;
}

/** 依次尝试一组候选 selector，返回第一个 attached 的 locator（隐藏 input 也能拿到）。 */
async function firstAttached(page, selectors, timeout) {
  const per = Math.max(1500, Math.floor(timeout / selectors.length));
  for (const sel of selectors) {
    const loc = page.locator(sel).first();
    try {
      await loc.waitFor({ state: 'attached', timeout: per });
      return loc;
    } catch { /* 试下一个候选 */ }
  }
  return null;
}

/** 稳健点击：多候选 + 失败重试 1 次。成功返回 true。 */
async function clickFirst(page, selectors, timeout, label) {
  for (let attempt = 0; attempt < 2; attempt++) {
    const loc = await firstVisible(page, selectors, timeout);
    if (loc) {
      try {
        await loc.scrollIntoViewIfNeeded().catch(() => {});
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

/** 检测是否已登录：任一 loggedIn 信号出现即为真。 */
async function isLoggedIn(page, timeout = 8000) {
  const loc = await firstVisible(page, SELECTORS.loggedIn, timeout);
  return loc !== null;
}

/**
 * 确保已登录。未登录则停在登录页提示扫码，轮询直到登录或超时。
 * 抖音扫码后可能还有短信验证步骤，这里不自动处理（交给用户在窗口里完成），
 * 只要最终检测到登录信号即视为成功。返回 true/false。
 */
async function ensureLogin(page, timeout) {
  await page.goto(DEFAULTS.homeUrl, { waitUntil: 'domcontentloaded' }).catch(() => {});
  await sleep(1500);
  if (await isLoggedIn(page, 6000)) {
    log('✅ 已是登录态（复用持久化会话）');
    return true;
  }

  log('🔐 未检测到登录态，请在浏览器窗口完成登录…');
  // 登出态落地页通常要先点「登录」才弹出二维码
  let qr = await firstVisible(page, SELECTORS.qrcode, 4000);
  if (!qr) {
    await clickFirst(page, SELECTORS.loginEntry, 5000, '「登录」入口');
    await sleep(1500);
    qr = await firstVisible(page, SELECTORS.qrcode, 5000);
  }
  if (qr) {
    log('📱 请用抖音 App 扫描窗口中的二维码完成登录（如需短信验证，请在窗口内操作）…');
  } else {
    log('📱 请在打开的浏览器窗口中完成登录（点「登录」并扫码）…');
  }

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
 * 切换到上传页：若不在 content/upload，点「高清发布」按钮并等 URL 切换。
 * 成功返回 true。
 */
async function goUploadPage(page, timeout) {
  if (page.url().includes('content/upload')) return true;
  const clicked = await clickFirst(page, SELECTORS.hdPublishBtn, timeout, '「高清发布」按钮');
  if (!clicked) {
    // 兜底：直接导航到上传页 URL
    await page.goto(DEFAULTS.uploadUrl, { waitUntil: 'domcontentloaded' }).catch(() => {});
  }
  try {
    await page.waitForURL(/content\/upload/, { timeout });
    await sleep(800);
    return true;
  } catch {
    return page.url().includes('content/upload');
  }
}

/**
 * 切到「发布图文」tab。等 tab 渲染出来后点击；用「出现图片 file input」作为成功判据。
 * 成功返回 true。
 */
async function switchToImageTextTab(page, timeout) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    // 等 tab 出现
    const tab = await firstVisible(page, SELECTORS.tabImageText, 3000);
    if (tab) {
      await tab.click({ force: true }).catch(() => {});
      await sleep(1200);
    }
    // 成功判据：出现「上传图文」按钮或图片 file input
    const btn = await firstVisible(page, SELECTORS.uploadImageTextBtn, 2500);
    if (btn) return true;
    const input = await firstAttached(page, SELECTORS.uploadFileInput, 1500);
    if (input) return true;
    await sleep(800);
  }
  return false;
}

// ─── Publish flow ────────────────────────────────────────────────────────────

/**
 * 自动选「推荐」第一首配乐：点「选择音乐」入口 → 等推荐列表 → hover 第一首歌曲项
 * → 点浮现的「使用」按钮。成功返回 true；任何一步失败返回 false（调用方降级，不阻断发布）。
 * 「使用」按钮仅在 hover 歌曲项时浮现，故用 mouse.move 到歌曲项中心再点。
 */
async function selectRecommendedMusic(page, timeout) {
  // 1) 打开音乐面板
  const entry = await firstVisible(page, SELECTORS.musicEntry, 6000);
  if (!entry) return false;
  await entry.click().catch(() => {});
  await sleep(3000);

  // 2) 确保在「推荐」tab（默认就是，点一下更稳）
  const tab = await firstVisible(page, SELECTORS.musicRecommendTab, 4000);
  if (tab) { await tab.click().catch(() => {}); await sleep(1500); }

  // 3) 等推荐歌曲项渲染，取第一首可见项
  let song = null;
  const deadline = Date.now() + Math.max(timeout, 8000);
  while (Date.now() < deadline && !song) {
    for (const sel of SELECTORS.musicSongItem) {
      const loc = page.locator(sel).first();
      try {
        await loc.waitFor({ state: 'visible', timeout: 2000 });
        const box = await loc.boundingBox();
        if (box && box.width > 0 && box.height > 10) { song = { loc, box }; break; }
      } catch { /* 试下一个候选 */ }
    }
    if (!song) await sleep(1000);
  }
  if (!song) return false;

  // 4) hover 第一首 → 浮现「使用」按钮 → 点击
  await page.mouse.move(song.box.x + song.box.width / 2, song.box.y + song.box.height / 2);
  await sleep(1200);
  const useBtn = await firstVisible(page, SELECTORS.musicUseBtn, 4000);
  if (!useBtn) return false;
  await useBtn.click().catch(() => {});
  await sleep(1500);
  return true;
}

/**
 * 勾选「自主声明 = 内容由AI生成」。AI 生成内容不声明会被判违规/限流，所以这步默认开启。
 * 流程：点「请选择自主声明」入口 → 弹窗里选「内容由AI生成」单选 → 点「确定」(选中后才可点)。
 * 成功返回 true；任何一步失败返回 false（调用方会明确警告，因为漏声明有合规风险）。
 */
async function selectAIDeclaration(page, timeout) {
  // 1) 打开声明弹窗
  const entry = await firstVisible(page, SELECTORS.declareEntry, 6000);
  if (!entry) return false;
  await entry.scrollIntoViewIfNeeded().catch(() => {});
  await entry.click().catch(() => {});
  await sleep(2500);

  // 2) 选「内容由AI生成」单选项
  const opt = await firstVisible(page, SELECTORS.declareAIOption, 5000);
  if (!opt) return false;
  await opt.click().catch(() => {});
  await sleep(1000);

  // 3) 点「确定」（页面可能同时存在多个「确定」，取最后一个=弹窗内的）
  let confirmed = false;
  for (const sel of SELECTORS.declareConfirmBtn) {
    const btn = page.locator(sel).last();
    try {
      if (await btn.isVisible()) { await btn.click({ timeout: 4000 }); confirmed = true; break; }
    } catch { /* 试下一个候选 */ }
  }
  if (!confirmed) return false;
  await sleep(1500);

  // 4) 校验声明栏已显示「内容由AI生成」
  const ok = await page.evaluate(() =>
    [...document.querySelectorAll('[class*="selectText"],[class*="declaraton"],[class*="controlWrapper"]')]
      .some((e) => /内容由AI生成/.test(e.innerText || ''))
  ).catch(() => false);
  return ok;
}

/**
 * 发布主流程：进上传页 → 切「发布图文」tab → 上传图片 → 填标题/简介 → 停在发布按钮。
 * 传 cfg.publish 才真正点击发布。返回 { ok, stopped, published, message, screenshot }。
 */
async function runPublish(page, cfg) {
  // 1) 进入上传页
  const onUpload = await goUploadPage(page, cfg.timeout);
  if (!onUpload) {
    return { ok: false, message: '未能进入上传页（「高清发布」按钮失效或页面结构变化，见 SELECTORS）' };
  }
  await sleep(1000);

  // 2) 切到「发布图文」tab
  const switched = await switchToImageTextTab(page, 12000);
  if (!switched) {
    log('⚠️  未能确认切到「发布图文」tab，继续尝试定位图片上传入口…');
  }
  await sleep(800);

  // 3) 上传图片：优先点「上传图文」按钮触发 filechooser；拿不到则直接喂隐藏 input。
  const paths = cfg.images.map((p) => resolve(p));
  let uploaded = false;
  const uploadBtn = await firstVisible(page, SELECTORS.uploadImageTextBtn, 4000);
  if (uploadBtn) {
    try {
      const [chooser] = await Promise.all([
        page.waitForEvent('filechooser', { timeout: 6000 }),
        uploadBtn.click(),
      ]);
      await chooser.setFiles(paths);
      uploaded = true;
      log(`📤 已通过文件选择器提交 ${paths.length} 张图片`);
    } catch { /* 退回直接喂 input */ }
  }
  if (!uploaded) {
    const input = await firstAttached(page, SELECTORS.uploadFileInput, cfg.timeout);
    if (!input) {
      return { ok: false, message: '找不到图片上传入口（uploadImageTextBtn / uploadFileInput selector 可能已失效）' };
    }
    try {
      await input.setInputFiles(paths);
      uploaded = true;
      log(`📤 已向隐藏 input 提交 ${paths.length} 张图片`);
    } catch (e) {
      return { ok: false, message: `图片上传失败: ${e.message}` };
    }
  }

  // 4) 等编辑页就绪（标题框出现）
  const titleBox = await firstVisible(page, SELECTORS.titleInput, cfg.timeout);
  if (!titleBox) {
    return { ok: false, message: '上传后未进入编辑页（标题框未出现，可能图片仍在上传或 selector 失效）' };
  }

  // 5) 填标题（标准 input：聚焦 → 全选清空 → 输入）
  try {
    await titleBox.click();
    await page.keyboard.press('Control+A').catch(() => {});
    await titleBox.fill('');
    await titleBox.type(cfg.title, { delay: 20 });
    log(`📝 标题已填：「${cfg.title}」(${[...cfg.title].length} 字)`);
  } catch (e) {
    return { ok: false, message: `填写标题失败: ${e.message}` };
  }

  // 6) 填简介（slate contenteditable）+ 话题（末尾追加 #tag，抖音无独立话题下拉）
  const editor = await firstVisible(page, SELECTORS.descriptionInput, cfg.timeout);
  if (!editor) {
    return { ok: false, message: '找不到作品简介编辑区（descriptionInput selector 可能已失效）' };
  }
  try {
    let body = cfg.content;
    if (cfg.topics.length) {
      body += ' ' + cfg.topics.map((t) => `#${t}`).join(' ');
    }
    await editor.click();
    await editor.type(body, { delay: 8 });
    log(`📝 简介已填（${[...body].length} 字）${cfg.topics.length ? '，含话题 ' + cfg.topics.map((t) => '#' + t).join(' ') : ''}`);
  } catch (e) {
    return { ok: false, message: `填写简介失败: ${e.message}` };
  }

  await sleep(1000);

  // 6.5) 自动选「推荐」第一首配乐（默认开启；--no-music 关闭）。失败仅警告，不阻断发布。
  if (cfg.music) {
    try {
      const ok = await selectRecommendedMusic(page, cfg.timeout);
      if (ok) log('🎵 已选用「推荐」第一首配乐');
      else log('⚠️  未能自动选配乐（入口/列表/「使用」按钮 selector 可能已变），将不带配乐继续');
    } catch (e) {
      log(`⚠️  自动配乐异常：${e.message}，将不带配乐继续`);
    }
    await sleep(800);
  }

  // 6.6) 勾选「自主声明 = 内容由AI生成」（默认开启；--no-ai-declare 关闭）。
  //      AI 生成内容不声明会被判违规/限流，所以失败时给出明确警告（而非静默）。
  if (cfg.aiDeclare) {
    try {
      const ok = await selectAIDeclaration(page, cfg.timeout);
      if (ok) log('✅ 已勾选自主声明：内容由AI生成');
      else log('⚠️  未能勾选「内容由AI生成」声明（selector 可能已变）！AI 内容未声明有违规风险，请在窗口内手动选择。');
    } catch (e) {
      log(`⚠️  勾选AI声明异常：${e.message}！请在窗口内手动选择「内容由AI生成」。`);
    }
    await sleep(800);
  }

  // 7) 定位「发布」按钮：在卡片容器里找文本严格等于「发布」的 button，滚到视图中心
  const container = await firstAttached(page, SELECTORS.publishContainer, cfg.timeout);
  if (!container) {
    return { ok: false, message: '找不到发布卡片容器（publishContainer selector 可能已失效）' };
  }
  const publishBtn = container.locator('button', { hasText: /^发布$/ }).first();
  try {
    await publishBtn.waitFor({ state: 'attached', timeout: 5000 });
    await publishBtn.scrollIntoViewIfNeeded().catch(() => {});
  } catch {
    return { ok: false, message: '未在卡片容器内找到「发布」按钮（文本匹配失败，可能改版）' };
  }

  // 8) 截图（无论停手还是发布，先留证据）
  const shotPath = cfg.screenshot
    || join(tmpdir(), `douyin-publish-${new Date().toISOString().replace(/[:.]/g, '-')}.png`);
  await page.screenshot({ path: shotPath, fullPage: true }).catch(() => {});

  if (!cfg.publish) {
    return {
      ok: true, stopped: true, published: false, screenshot: shotPath,
      message: '已到编辑页并填好内容，停在「发布」按钮。请在浏览器中人工确认后点击发布。',
    };
  }

  // 9) 显式 --publish 才真正发布。
  //    注意：发布按钮带 position:fixed 类，且在长表单底部（文档坐标 y 很大）。
  //    Playwright 的 scrollIntoViewIfNeeded()+.click() 对它会落点错误、点了不发布。
  //    可靠做法：用页面内 JS scrollIntoView({block:'center'}) 把它滚到视口中央，
  //    再用 page.mouse.click 点重算后的真实中心坐标。
  try {
    const center = await publishBtn.evaluate((el) => {
      el.scrollIntoView({ block: 'center', inline: 'center' });
      const b = el.getBoundingClientRect();
      return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
    });
    await sleep(400);
    await page.mouse.click(center.x, center.y);
  } catch (e) {
    return { ok: false, screenshot: shotPath, message: `点击发布失败: ${e.message}（请人工点击）` };
  }

  // 10) 检测 toast 判断结果。「正在发布」是进行中状态（需继续等），「发布成功」才算成功；
  //     其它非空 toast 视为失败原因。跳转到作品管理页也兜底视为成功。
  let published = false;
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    await sleep(1000);
    const toast = await firstVisible(page, SELECTORS.publishToast, 1500);
    if (toast) {
      const text = (await toast.textContent().catch(() => '') || '').trim();
      if (text.includes('发布成功')) { published = true; break; }
      if (text.includes('正在发布') || text.includes('上传中') || text.includes('处理中')) {
        continue; // 进行中，继续等
      }
      if (text) {
        return { ok: false, screenshot: shotPath, message: `发布失败：${text}` };
      }
    }
    // 兜底：跳转到作品管理页也视为成功
    if (/content\/manage/.test(page.url())) { published = true; break; }
  }
  if (published) {
    return { ok: true, published: true, screenshot: shotPath, message: '发布成功 🎉' };
  }
  return {
    ok: true, published: false, screenshot: shotPath,
    message: '已点击发布，但未捕获到成功提示。请在浏览器/创作后台确认是否发布成功。',
  };
}

// PLACEHOLDER_MAIN

// ─── Validation ──────────────────────────────────────────────────────────────

/** 校验参数；返回错误信息数组（空=通过）。同时读 content-file/prompt-file 并推导标题/简介。 */
async function validate(cfg) {
  const errors = [];

  // 图片来源：--image（已有图）或 --prompt/--prompt-file（先生成）
  cfg.willGenerate = false;
  if (cfg.images.length) {
    for (const img of cfg.images) {
      if (!(await fileExists(resolve(img)))) errors.push(`图片不存在: ${img}`);
    }
  } else if (cfg.prompt || cfg.promptFile) {
    cfg.willGenerate = true;
  } else {
    errors.push('缺少图片：请用 --image 指定已有图，或用 --prompt/--prompt-file 让脚本先生成');
  }

  // prompt 文本来源：--prompt 优先，否则读 --prompt-file
  let promptText = cfg.prompt || null;
  if (!promptText && cfg.promptFile) {
    if (!(await fileExists(resolve(cfg.promptFile)))) {
      errors.push(`prompt 文件不存在: ${cfg.promptFile}`);
    } else {
      promptText = await readPromptFile(cfg.promptFile);
      if (!promptText) errors.push(`无法从 prompt 文件解析内容: ${cfg.promptFile}`);
    }
  }
  cfg.promptText = promptText;

  // 简介：--content > --content-file > 由 prompt 精简推导
  cfg.contentSource = 'arg';
  if (!cfg.content && cfg.contentFile) {
    if (!(await fileExists(resolve(cfg.contentFile)))) {
      errors.push(`简介文件不存在: ${cfg.contentFile}`);
    } else {
      try {
        cfg.content = (await readFile(resolve(cfg.contentFile), 'utf8')).trim();
        cfg.contentSource = 'file';
      } catch (e) {
        errors.push(`读取简介文件失败: ${e.message}`);
      }
    }
  }
  if (!cfg.content && promptText) {
    cfg.content = deriveContent(promptText, 100);
    cfg.contentSource = 'prompt';
  }
  if (!cfg.content) {
    errors.push('缺少简介：请用 --content / --content-file 指定，或用 --prompt/--prompt-file 自动精简');
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
    errors.push(`标题超长：${[...cfg.title].length} 字 > ${DEFAULTS.titleMaxLen} 字上限，请压缩后重试`);
  }

  return errors;
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const cfg = parseArgs();

  if (cfg.help) { printHelp(); process.exit(0); }

  console.log('='.repeat(50));
  console.log('🎵 抖音图文发布');
  console.log('='.repeat(50));

  const errors = await validate(cfg);
  if (errors.length) {
    console.error('\n❌ 参数校验未通过：');
    for (const e of errors) console.error(`   - ${e}`);
    printHelp();
    process.exit(1);
  }

  // dry-run：只打印参数与步骤，不启动浏览器
  if (cfg.dryRun) {
    const tSrc = { arg: '(--title)', prompt: '(按图片风格自动生成)' }[cfg.titleSource] || '';
    const cSrc = { arg: '(--content)', file: '(--content-file)', prompt: '(prompt 精简)' }[cfg.contentSource] || '';
    console.log('\n🔍 DRY-RUN（不启动浏览器）');
    if (cfg.willGenerate) {
      console.log(`   图片: 待生成（provider=${cfg.provider}, ar=${cfg.aspectRatio}）`);
      console.log(`   生图 prompt: ${cfg.promptText.slice(0, 60).replace(/\n/g, ' ')}${cfg.promptText.length > 60 ? '…' : ''}`);
    } else {
      console.log(`   图片(${cfg.images.length}): ${cfg.images.join(', ')}`);
    }
    console.log(`   标题: 「${cfg.title}」(${[...cfg.title].length} 字) ${tSrc}`);
    const preview = cfg.content.length > 100 ? cfg.content.slice(0, 100) + '…' : cfg.content;
    console.log(`   简介: ${preview.replace(/\n/g, ' ')} (${[...cfg.content].length} 字) ${cSrc}`);
    console.log(`   话题: ${cfg.topics.length ? cfg.topics.map((t) => '#' + t).join(' ') + '（追加到简介末尾）' : '(无)'}`);
    console.log(`   配乐: ${cfg.music ? '自动选「推荐」第一首' : '不配乐（--no-music）'}`);
    console.log(`   自主声明: ${cfg.aiDeclare ? '内容由AI生成' : '不声明（--no-ai-declare）'}`);
    console.log(`   发布行为: ${cfg.publish ? '自动点击发布' : '停在发布按钮（默认，需人工确认）'}`);
    console.log(`   登录态目录: ${cfg.userDataDir}`);
    console.log('\n将执行步骤：'
      + (cfg.willGenerate ? '生成图片 → ' : '')
      + '登录校验 → 进上传页 → 切发布图文 tab → 上传图片 → 填标题/简介 → '
      + (cfg.music ? '选推荐配乐 → ' : '')
      + (cfg.aiDeclare ? '勾选AI生成声明 → ' : '')
      + (cfg.publish ? '点击发布' : '停在发布按钮并截图'));
    process.exit(0);
  }

  // 生成即发布：没有 --image 但有 prompt → 先生图
  if (cfg.willGenerate) {
    const output = cfg.output || join(
      tmpdir(),
      `douyin-image-${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
    );
    const gen = await generateImage(cfg.promptText, output, cfg.aspectRatio, cfg.provider);
    if (!gen.ok) { console.error(`\n❌ ${gen.message}`); process.exit(1); }
    cfg.images = [gen.path];
    const sizeKB = Math.round((await stat(gen.path)).size / 1024);
    console.log(`✅ 图片已生成: ${gen.path} (${sizeKB} KB)`);
  }

  await mkdir(cfg.userDataDir, { recursive: true }).catch(() => {});

  // 懒加载 playwright
  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch {
    console.error('\n❌ 未安装 playwright。请在技能目录执行：');
    console.error('     npm install            # 安装 playwright 依赖');
    console.error('     npm run setup:xhs      # 安装 Chromium 内核（playwright install chromium）');
    process.exit(1);
  }

  // 抖音的「发布」在无头(headless)模式下会被反自动化拦截：点击后稳定卡在「正在发布」
  // 永不完成（实测无头 4 次均未落地，可见窗口一次成功并跳转作品管理页）。
  // 因此只要真正发布(--publish)，就强制可见窗口；仅停在按钮(默认)或 --dry-run 不受影响。
  let headless = !cfg.headed;
  if (cfg.publish && headless) {
    console.log('ℹ️  抖音发布需可见窗口（无头模式会被反自动化拦截卡在「正在发布」），已自动切换为 headed。');
    headless = false;
  }
  const launchOpts = {
    headless,
    viewport: { width: 1280, height: 900 },
    args: ['--disable-blink-features=AutomationControlled'],
  };

  let context;
  try {
    context = await chromium.launchPersistentContext(cfg.userDataDir, launchOpts);
  } catch (e) {
    console.error(`\n❌ 启动 Chromium 失败: ${e.message}`);
    console.error('   可能未安装内核，请先执行： npx playwright install chromium');
    process.exit(1);
  }

  const page = context.pages()[0] || (await context.newPage());
  page.setDefaultTimeout(cfg.timeout);

  let exitCode = 0;
  try {
    let loggedIn = await ensureLogin(page, DEFAULTS.loginTimeout);

    // 无头模式下未登录无法扫码：重启为可见窗口再试一次
    if (!loggedIn && headless) {
      console.log('\n⚠️  无头模式无法扫码登录，正在切换为可见窗口重试…');
      await context.close().catch(() => {});
      context = await chromium.launchPersistentContext(cfg.userDataDir, { ...launchOpts, headless: false });
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
    await sleep(cfg.publish ? 500 : 1500);
    await context.close().catch(() => {});
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






