#!/usr/bin/env node

/**
 * 工作空间管理工具
 *
 * 功能：
 *  - 初始化诗词工作空间目录结构
 *  - 创建和更新 .workflow-state.json
 *  - 扫描和恢复未完成的工作
 *  - 生成交付清单
 *
 * 用法：
 *   workspace-manager.js init <诗词名> [--author 作者] [--dynasty 朝代]
 *   workspace-manager.js update <诗词名> <阶段> <状态> [--output 文件]
 *   workspace-manager.js resume [--workspace 路径]
 *   workspace-manager.js list
 *   workspace-manager.js report <诗词名>
 */

import { mkdir, writeFile, readFile, readdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve, join, basename } from 'node:path';

// ─── 配置 ────────────────────────────────────────────────────────────────────

// 工作空间根目录：当前工作目录下的 release/（已存在则复用，不新建）
const WORKSPACE_ROOT = 'release';

const STRUCTURE = {
  imgs: {
    prompts: null,  // 空对象表示叶子目录
  },
  html: null,
  published: null,
};

// ─── 工具函数 ─────────────────────────────────────────────────────────────────

/** 清理诗词名：去除书名号、空格、括号内容 */
function sanitizePoemName(name) {
  return name
    .replace(/[《》「」『』【】\[\]()（）]/g, '')
    .replace(/\s+/g, '')
    .trim();
}

/** 生成工作流 ID：YYYYMMDD-NNN */
function generateWorkflowId() {
  const now = new Date();
  const date = now.toISOString().slice(0, 10).replace(/-/g, '');
  const seq = String(Math.floor(Math.random() * 1000)).padStart(3, '0');
  return `${date}-${seq}`;
}

/** 递归创建目录结构 */
async function createStructure(basePath, structure) {
  for (const [name, children] of Object.entries(structure)) {
    const path = join(basePath, name);
    await mkdir(path, { recursive: true });
    if (children && typeof children === 'object') {
      await createStructure(path, children);
    }
  }
}

/** 读取 workflow state，不存在返回 null */
async function readWorkflowState(poemDir) {
  const statePath = join(poemDir, '.workflow-state.json');
  if (!existsSync(statePath)) return null;
  try {
    return JSON.parse(await readFile(statePath, 'utf-8'));
  } catch {
    return null;
  }
}

/** 写入 workflow state */
async function writeWorkflowState(poemDir, state) {
  const statePath = join(poemDir, '.workflow-state.json');
  await writeFile(statePath, JSON.stringify(state, null, 2), 'utf-8');
}

/** 扫描工作空间根目录，返回所有诗词目录及其状态 */
async function scanWorkspaces(cwd = process.cwd()) {
  const root = join(cwd, WORKSPACE_ROOT);
  if (!existsSync(root)) return [];

  const entries = await readdir(root, { withFileTypes: true });
  const workspaces = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const poemDir = join(root, entry.name);
    const state = await readWorkflowState(poemDir);
    const stats = await stat(poemDir);
    workspaces.push({
      poem: entry.name,
      path: poemDir,
      state,
      mtime: stats.mtimeMs,
    });
  }

  return workspaces.sort((a, b) => b.mtime - a.mtime);
}

/** 统计工作空间文件 */
async function statWorkspace(poemDir) {
  const result = {
    content: null,
    metadata: null,
    images: [],
    html: [],
    published: [],
  };

  try {
    const files = await readdir(poemDir);
    for (const f of files) {
      if (f.endsWith('.md') && !f.startsWith('.')) result.content = f;
      if (f === 'poem-metadata.json') result.metadata = f;
    }

    const imgsDir = join(poemDir, 'imgs');
    if (existsSync(imgsDir)) {
      const imgs = await readdir(imgsDir);
      result.images = imgs.filter(f => /\.(png|jpe?g|webp)$/i.test(f));
    }

    const htmlDir = join(poemDir, 'html');
    if (existsSync(htmlDir)) {
      const htmls = await readdir(htmlDir);
      result.html = htmls.filter(f => f.endsWith('.html'));
    }

    const pubDir = join(poemDir, 'published');
    if (existsSync(pubDir)) {
      const pubs = await readdir(pubDir);
      result.published = pubs.filter(f => f.endsWith('.json'));
    }
  } catch {}

  return result;
}

// ─── 命令实现 ─────────────────────────────────────────────────────────────────

async function cmdInit(poem, opts) {
  const sanitized = sanitizePoemName(poem);
  const poemDir = resolve(WORKSPACE_ROOT, sanitized);

  if (existsSync(poemDir)) {
    console.log(`⚠️  工作空间已存在：${poemDir}`);
    const existing = await readWorkflowState(poemDir);
    if (existing) {
      console.log(`当前状态：${JSON.stringify(existing.stages, null, 2)}`);
    }
    return;
  }

  // 创建目录结构
  await mkdir(poemDir, { recursive: true });
  await createStructure(poemDir, STRUCTURE);

  // 初始化 workflow state
  const state = {
    poem: sanitized,
    author: opts.author || null,
    dynasty: opts.dynasty || null,
    workflow_id: generateWorkflowId(),
    created_at: new Date().toISOString(),
    stages: {
      writing: { status: 'pending' },
      illustration: { status: 'pending' },
      html_conversion: { status: 'pending' },
      publishing: { status: 'pending' },
    },
    next_action: '开始创作内容',
    last_error: null,
  };

  await writeWorkflowState(poemDir, state);

  console.log(`✅ 工作空间已创建：${poemDir}`);
  console.log(`📋 工作流 ID：${state.workflow_id}`);
  console.log(`📁 目录结构：`);
  console.log(`   ├── imgs/prompts/`);
  console.log(`   ├── html/`);
  console.log(`   ├── published/`);
  console.log(`   └── .workflow-state.json`);
}

async function cmdUpdate(poem, stage, status, opts) {
  const sanitized = sanitizePoemName(poem);
  const poemDir = resolve(WORKSPACE_ROOT, sanitized);

  if (!existsSync(poemDir)) {
    console.error(`❌ 工作空间不存在：${poemDir}`);
    console.error(`提示：先运行 workspace-manager.js init "${poem}"`);
    process.exit(1);
  }

  const state = await readWorkflowState(poemDir);
  if (!state) {
    console.error(`❌ 无法读取 .workflow-state.json`);
    process.exit(1);
  }

  if (!state.stages[stage]) {
    console.error(`❌ 未知阶段：${stage}`);
    console.error(`可用阶段：${Object.keys(state.stages).join(', ')}`);
    process.exit(1);
  }

  state.stages[stage].status = status;
  if (opts.output) state.stages[stage].output = opts.output;
  state.updated_at = new Date().toISOString();

  // 自动推断 next_action
  const stageOrder = ['writing', 'illustration', 'html_conversion', 'publishing'];
  const currentIdx = stageOrder.indexOf(stage);
  if (status === 'completed' && currentIdx < stageOrder.length - 1) {
    const nextStage = stageOrder[currentIdx + 1];
    const actionMap = {
      illustration: '生成配图',
      html_conversion: '转换 HTML',
      publishing: '发布到公众号',
    };
    state.next_action = actionMap[nextStage] || '继续';
  } else if (status === 'completed' && currentIdx === stageOrder.length - 1) {
    state.next_action = '已完成';
  }

  await writeWorkflowState(poemDir, state);
  console.log(`✅ 已更新：${stage} → ${status}`);
  console.log(`📍 下一步：${state.next_action}`);
}

async function cmdResume(opts) {
  const workspaces = await scanWorkspaces(opts.workspace || process.cwd());

  if (workspaces.length === 0) {
    console.log('🔍 未找到工作空间');
    console.log(`提示：工作空间根目录应为 ${WORKSPACE_ROOT}/`);
    return;
  }

  const incomplete = workspaces.filter(w => {
    if (!w.state) return false;
    const stages = Object.values(w.state.stages);
    return stages.some(s => s.status === 'in_progress' || s.status === 'pending');
  });

  if (incomplete.length === 0) {
    console.log('✅ 所有工作空间都已完成');
    return;
  }

  console.log(`\n🔄 检测到 ${incomplete.length} 个未完成的工作空间：\n`);

  for (const ws of incomplete) {
    const { poem, state } = ws;
    const stages = Object.entries(state.stages);
    const completed = stages.filter(([, s]) => s.status === 'completed').length;
    const total = stages.length;

    console.log(`📋 《${poem}》`);
    console.log(`   进度：${completed}/${total}`);
    console.log(`   下一步：${state.next_action}`);
    if (state.last_error) {
      console.log(`   ⚠️  上次错误：${state.last_error}`);
    }
    console.log(`   路径：${ws.path}`);
    console.log('');
  }

  console.log(`💡 恢复提示：在对话中说"继续《${incomplete[0].poem}》"即可恢复`);
}

async function cmdList() {
  const workspaces = await scanWorkspaces();

  if (workspaces.length === 0) {
    console.log('🔍 未找到工作空间');
    return;
  }

  console.log(`\n📁 共 ${workspaces.length} 个工作空间（按最近修改排序）：\n`);

  for (const ws of workspaces) {
    const { poem, state, mtime } = ws;
    const date = new Date(mtime).toISOString().slice(0, 19).replace('T', ' ');

    if (!state) {
      console.log(`📄 ${poem} (${date}) - 无状态文件`);
      continue;
    }

    const stages = Object.entries(state.stages);
    const completed = stages.filter(([, s]) => s.status === 'completed').length;
    const total = stages.length;
    const progress = completed === total ? '✅' : `${completed}/${total}`;

    console.log(`📄 ${poem} (${date}) - ${progress}`);
  }

  console.log('');
}

async function cmdReport(poem) {
  const sanitized = sanitizePoemName(poem);
  const poemDir = resolve(WORKSPACE_ROOT, sanitized);

  if (!existsSync(poemDir)) {
    console.error(`❌ 工作空间不存在：${poemDir}`);
    process.exit(1);
  }

  const state = await readWorkflowState(poemDir);
  const files = await statWorkspace(poemDir);

  console.log(`\n✅ 《${poem}》交付清单\n`);
  console.log(`📁 工作空间：${poemDir}`);

  if (state) {
    console.log(`📋 工作流 ID：${state.workflow_id}`);
    const stages = Object.entries(state.stages);
    const completed = stages.filter(([, s]) => s.status === 'completed').length;
    console.log(`📊 完成进度：${completed}/${stages.length}`);
  }

  console.log('');

  if (files.content) {
    const size = (await stat(join(poemDir, files.content))).size;
    console.log(`📄 内容文件：${files.content} (${(size / 1024).toFixed(1)} KB)`);
  }

  if (files.metadata) {
    console.log(`📋 元数据：${files.metadata}`);
  }

  if (files.images.length > 0) {
    console.log(`🖼️  配图：${files.images.length} 张`);
    for (const img of files.images) {
      console.log(`   - ${img}`);
    }
  }

  if (files.html.length > 0) {
    console.log(`🌐 HTML：${files.html.join(', ')}`);
  }

  if (files.published.length > 0) {
    console.log(`📮 发布信息：${files.published.join(', ')}`);
  }

  console.log('');

  if (state && state.next_action !== '已完成') {
    console.log(`📍 下一步：${state.next_action}`);
  }
}

// ─── CLI ───────────────────────────────────────────────────────────────────────

function showHelp() {
  console.log(`
工作空间管理工具

用法：
  workspace-manager.js init <诗词名> [选项]      初始化工作空间
  workspace-manager.js update <诗词名> <阶段> <状态> [选项]  更新阶段状态
  workspace-manager.js resume [选项]            恢复未完成的工作
  workspace-manager.js list                     列出所有工作空间
  workspace-manager.js report <诗词名>          生成交付清单

命令：
  init      创建诗词工作空间，初始化目录结构和状态文件
  update    更新工作流阶段状态（writing/illustration/html_conversion/publishing）
  resume    扫描并显示未完成的工作空间
  list      列出所有工作空间及其进度
  report    生成指定诗词的交付清单

选项（init）：
  --author <作者>    诗人姓名
  --dynasty <朝代>   朝代

选项（update）：
  --output <文件>    该阶段的输出文件

选项（resume）：
  --workspace <路径> 指定工作空间根目录（默认当前目录）

阶段状态：
  pending       待处理
  in_progress   进行中
  completed     已完成
  failed        失败

示例：
  # 初始化《静夜思》工作空间
  workspace-manager.js init 静夜思 --author 李白 --dynasty 唐

  # 标记写作阶段完成
  workspace-manager.js update 静夜思 writing completed --output 《静夜思》_古诗词鉴赏_中文版.md

  # 扫描未完成的工作
  workspace-manager.js resume

  # 生成交付清单
  workspace-manager.js report 静夜思
`);
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    showHelp();
    process.exit(0);
  }

  const command = args[0];
  const opts = {};

  // 简单的参数解析
  for (let i = 1; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      opts[key] = args[++i] || true;
    }
  }

  try {
    switch (command) {
      case 'init':
        if (args.length < 2) {
          console.error('错误：缺少诗词名');
          showHelp();
          process.exit(1);
        }
        await cmdInit(args[1], opts);
        break;

      case 'update':
        if (args.length < 4) {
          console.error('错误：用法 update <诗词名> <阶段> <状态>');
          process.exit(1);
        }
        await cmdUpdate(args[1], args[2], args[3], opts);
        break;

      case 'resume':
        await cmdResume(opts);
        break;

      case 'list':
        await cmdList();
        break;

      case 'report':
        if (args.length < 2) {
          console.error('错误：缺少诗词名');
          process.exit(1);
        }
        await cmdReport(args[1]);
        break;

      default:
        console.error(`错误：未知命令 "${command}"`);
        showHelp();
        process.exit(1);
    }
  } catch (err) {
    console.error(`❌ 错误：${err.message}`);
    process.exit(1);
  }
}

main();
