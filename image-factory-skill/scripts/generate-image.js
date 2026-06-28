#!/usr/bin/env node

/**
 * Image generation script for article-illustration-tools
 *
 * Backends: codex-cli, gemini (agy)
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
 *   generate-image.js --batch tasks.json [--concurrency 3]
 *
 * batch tasks.json: [{"prompt-file":"p1.md","output":"a.png","aspect-ratio":"16:9"}, ...]
 */

import { spawn } from 'node:child_process';
import { readFile, writeFile, copyFile, stat, readdir, mkdir } from 'node:fs/promises';
import { resolve, dirname, basename, join } from 'node:path';
import { homedir, tmpdir } from 'node:os';

// ─── Config ─────────────────────────────────────────────────────────────────

const DEFAULTS = {
  provider: 'auto',
  aspectRatio: '16:9',
  timeoutMs: 5 * 60 * 1000,   // 5 minutes per image
  retries: 1,                  // 1 retry on failure
  concurrency: 3,              // for batch mode
};

const CODEX_GENERATED_DIR = join(homedir(), '.codex', 'generated_images');

// Process-wide set of codex source images already claimed by a task in this run.
// Prevents two concurrent batch tasks from copying the same source.
const CLAIMED_CODEX_SOURCES = new Set();

// ─── Argument parsing ───────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    provider: DEFAULTS.provider,
    promptFile: null,
    output: null,
    aspectRatio: DEFAULTS.aspectRatio,
    timeoutMs: DEFAULTS.timeoutMs,
    retries: DEFAULTS.retries,
    concurrency: DEFAULTS.concurrency,
    batch: null,
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
      case '--help': case '-h': showHelp(); process.exit(0);
      default:
        if (!cfg.promptFile && !a.startsWith('-')) cfg.promptFile = a;
    }
  }
  if (!cfg.batch && (!cfg.promptFile || !cfg.output)) {
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
  --provider, -p <auto|codex|gemini>   Backend selection (default: auto)
  --prompt-file <path>                 Prompt markdown file
  --output, -o <path>                  Output image path (verified after generation)
  --aspect-ratio, --ar <W:H>           Aspect ratio (default: 16:9)
  --timeout <seconds>                  Per-image timeout (default: 300)
  --retries <n>                        Retries on failure (default: 1)
  --concurrency <n>                    Parallel batch jobs (default: 3)
  --batch <tasks.json>                 JSON array of {prompt-file, output, aspect-ratio?}
  --help, -h                           Show this help

Backends:
  codex   — OpenAI Codex CLI (https://openai.com/zh-Hans-CN/codex)
  gemini  — Antigravity CLI (https://antigravity.google/docs/cli-getting-started)
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
  const out = { codex: false, gemini: false };
  try { await execCommand('which', ['codex'], { streamStderr: false }); out.codex = true; } catch {}
  try { await execCommand('which', ['agy'], { streamStderr: false }); out.gemini = true; } catch {}
  return out;
}

/** Extract the prompt body from a markdown file. Prefers a `PROMPT:` block. */
async function readPrompt(promptFile) {
  const content = await readFile(promptFile, 'utf-8');
  // Fix: use negative lookahead (?![\s\S]) to match true end-of-string, not end-of-line
  const m = content.match(/^PROMPT:\s*\n([\s\S]+?)(?=\n---|^\n##|(?![\s\S]))/m);
  if (m) return m[1].trim();

  // Fallback: strip frontmatter, return body.
  const lines = content.split('\n');
  let inFm = false, body = [];
  for (const line of lines) {
    if (line.trim() === '---') { inFm = !inFm; continue; }
    if (!inFm) body.push(line);
  }
  return body.join('\n').trim();
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

  // codex exec 偶尔以非零码退出（例如它内部的某个工具步骤报错），但图片其实已经
  // 写到了 ~/.codex/generated_images/<session>/。所以这里不让非零退出直接失败：
  // 先记下错误，照常走下面的"找回新生成图"逻辑；找到有效图就算成功，找不到才抛错。
  let execErr = null;
  try {
    await execCommand('codex', ['exec', '--skip-git-repo-check', fullPrompt], {
      streamStderr: opts.verbose,
      timeoutMs: opts.timeoutMs,
    });
  } catch (e) {
    execErr = e;
  }

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
    // 既没找回图，codex 又非零退出 → 这才是真失败，把底层错误一并抛出便于排查
    if (execErr) {
      throw new Error(`Codex 执行失败且未产出图片: ${execErr.message}`);
    }
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
    `Use the generate_image tool. Save the result and report the absolute path on the last line.`;

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

// ─── Orchestration ──────────────────────────────────────────────────────────

async function pickProvider(requested, available) {
  if (requested === 'auto') {
    if (available.codex) return 'codex';
    if (available.gemini) return 'gemini';
    throw new Error('No image generation backend available. Install codex-cli or agy.');
  }
  if (!available[requested]) {
    const tool = requested === 'codex' ? 'codex-cli' : 'agy (Antigravity CLI)';
    throw new Error(`Provider "${requested}" is not available. Install ${tool}.`);
  }
  return requested;
}

/** Run a single generation task with retries. */
async function runOne(task, providers, opts) {
  const provider = await pickProvider(task.provider || opts.provider, providers);
  const prompt = await readPrompt(task.promptFile);

  let lastErr = null;
  const maxAttempts = (opts.retries ?? DEFAULTS.retries) + 1;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const tag = `[${basename(task.output)}]`;
    const attemptLabel = maxAttempts > 1 ? ` (attempt ${attempt}/${maxAttempts})` : '';
    console.log(`${tag} Generating via ${provider}${attemptLabel}...`);
    try {
      const fn = provider === 'codex' ? generateWithCodex : generateWithGemini;
      const result = await fn(prompt, task.output, task.aspectRatio || opts.aspectRatio, {
        timeoutMs: opts.timeoutMs,
        verbose: opts.verbose ?? true,
      });
      console.log(`${tag} ✅ ${result.bytes} bytes → ${result.output}`);
      return { ok: true, ...result, promptFile: task.promptFile };
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
    }));
    for (const t of tasks) {
      if (!t.promptFile || !t.output) throw new Error('Each batch task needs prompt-file and output');
    }
    console.log(`Batch mode: ${tasks.length} tasks, concurrency=${cfg.concurrency}`);
  } else {
    tasks = [{ promptFile: cfg.promptFile, output: cfg.output, aspectRatio: cfg.aspectRatio }];
  }

  const opts = {
    provider: cfg.provider,
    aspectRatio: cfg.aspectRatio,
    timeoutMs: cfg.timeoutMs,
    retries: cfg.retries,
    concurrency: cfg.concurrency,
    verbose: !cfg.batch, // quieter in batch mode
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
