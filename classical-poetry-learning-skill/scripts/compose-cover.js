#!/usr/bin/env node

/**
 * Cover text compositor for classical poetry WeChat articles
 *
 * Composites title, author, dynasty, and representative poem lines onto
 * a text-free background image using Chrome headless + HTML/CSS rendering.
 *
 * Usage:
 *   compose-cover.js --meta poem-meta.json --background cover-bg.png --output cover-final.jpg
 *   compose-cover.js --meta poem-meta.json --background cover-bg.png --output cover.jpg --lines 2
 *   compose-cover.js --meta poem-meta.json --background cover-bg.png --output cover.jpg --lines full
 *
 * Options:
 *   --meta <path>          poem-meta.json (title, dynasty, author, lines)
 *   --background <path>    Background image (must have safe text area)
 *   --output <path>        Output path (jpg/png)
 *   --lines <n|full>       Number of poem lines to show (default: auto, "full" for all lines)
 *   --width <px>           Output width (default: from background, or 900)
 *   --height <px>          Output height (default: from background, or 383)
 *   --title-only           Only show title + author, no poem lines
 *   --help, -h             Show this help
 */

import { readFile, writeFile } from 'node:fs/promises';
import { resolve, dirname, basename, extname } from 'node:path';
import { spawn } from 'node:child_process';
import { tmpdir } from 'node:os';
import { createHash } from 'node:crypto';

// ─── Config ─────────────────────────────────────────────────────────────────

const CHROME_PATHS = process.platform === 'win32'
  ? [
      // Windows paths
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
      process.env.LOCALAPPDATA && process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe',
      'chrome',  // Fallback: search in PATH
    ].filter(Boolean)
  : process.platform === 'darwin'
  ? [
      // macOS paths
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      'chrome',
    ]
  : [
      // Linux paths
      '/usr/bin/google-chrome',
      '/usr/bin/chromium',
      'google-chrome',
      'chromium',
    ];

const FONT_PREFERENCES = [
  // macOS fonts
  'Songti SC',
  'STSong',
  // Windows fonts
  'SimSun',
  'Microsoft YaHei',
  'KaiTi',
  'FangSong',
  // Cross-platform fonts
  'Noto Serif SC',
  'Noto Sans SC',
  // Final fallback
  'serif',
];

// ─── Argument parsing ───────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    meta: null,
    background: null,
    output: null,
    lines: 'auto',
    width: null,
    height: null,
    titleOnly: false,
  };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    switch (a) {
      case '--meta': cfg.meta = args[++i]; break;
      case '--background': cfg.background = args[++i]; break;
      case '--output': cfg.output = args[++i]; break;
      case '--lines': cfg.lines = args[++i]; break;
      case '--width': cfg.width = parseInt(args[++i], 10); break;
      case '--height': cfg.height = parseInt(args[++i], 10); break;
      case '--title-only': cfg.titleOnly = true; break;
      case '--help': case '-h': showHelp(); process.exit(0);
      default:
        console.error(`Unknown option: ${a}`);
        showHelp();
        process.exit(1);
    }
  }
  if (!cfg.meta || !cfg.background || !cfg.output) {
    console.error('Error: --meta, --background, and --output are required');
    showHelp();
    process.exit(1);
  }
  return cfg;
}

function showHelp() {
  console.log(`
Usage:
  compose-cover.js --meta <poem-meta.json> --background <bg.png> --output <out.jpg> [options]

Options:
  --meta <path>          poem-meta.json with title, dynasty, author, lines
  --background <path>    Background image (must have clean safe area for text)
  --output <path>        Output image path
  --lines <n|full|auto>  Number of poem lines to display (default: auto)
                         "auto" picks 1-2 representative lines for long poems,
                         full text for short poems (≤4 lines)
                         "full" forces all lines to appear
                         A number picks that many lines
  --width <px>           Override output width (default: from background or 900)
  --height <px>          Override output height (default: from background or 383)
  --title-only           Only show title + author, no poem lines
  --help, -h             Show this help

Output:
  Composites text onto background and saves to --output path.
  Supports jpg/png. Recommend jpg with quality 90 for WeChat.
`);
}

// ─── Utilities ──────────────────────────────────────────────────────────────

async function getImageSize(path) {
  // Try to extract dimensions from image file (basic PNG/JPG header parsing)
  try {
    const buf = await readFile(path);
    // PNG: check signature + IHDR chunk
    if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4E && buf[3] === 0x47) {
      const width = buf.readUInt32BE(16);
      const height = buf.readUInt32BE(20);
      return { width, height };
    }
    // JPG: scan for SOF0/SOF2 markers (simplified, may not work for all JPEGs)
    if (buf[0] === 0xFF && buf[1] === 0xD8) {
      let i = 2;
      while (i < buf.length - 10) {
        if (buf[i] !== 0xFF) { i++; continue; }
        const marker = buf[i + 1];
        if (marker === 0xC0 || marker === 0xC2) {
          const height = buf.readUInt16BE(i + 5);
          const width = buf.readUInt16BE(i + 7);
          return { width, height };
        }
        const len = buf.readUInt16BE(i + 2);
        i += len + 2;
      }
    }
  } catch {}
  return { width: 900, height: 383 }; // fallback
}

async function findChrome() {
  for (const path of CHROME_PATHS) {
    try {
      await new Promise((res, rej) => {
        const child = spawn(path, ['--version'], { stdio: ['ignore', 'pipe', 'ignore'] });
        child.on('error', rej);
        child.on('close', code => code === 0 ? res() : rej());
      });
      return path;
    } catch {}
  }
  throw new Error(
    'Chrome/Chromium not found. Install Google Chrome or Chromium to use this script.'
  );
}

function execCommand(command, args, options = {}) {
  return new Promise((resolveP, rejectP) => {
    const child = spawn(command, args, {
      stdio: options.stdio || ['ignore', 'pipe', 'pipe'],
      cwd: options.cwd,
    });
    let stdout = '', stderr = '';
    if (child.stdout) child.stdout.on('data', d => { stdout += d.toString(); });
    if (child.stderr) child.stderr.on('data', d => { stderr += d.toString(); });
    child.on('error', rejectP);
    child.on('close', code => {
      if (code === 0) resolveP({ stdout, stderr, code });
      else rejectP(new Error(`Command failed (${code}): ${stderr.trim().slice(-300)}`));
    });
  });
}

// ─── Line selection logic ───────────────────────────────────────────────────

function selectLines(allLines, mode) {
  if (mode === 'full') return allLines;
  if (mode === 'auto') {
    // Short poems (≤4 lines): full text
    if (allLines.length <= 4) return allLines;
    // Long poems: pick 1-2 representative lines (first + one from middle/end)
    return [allLines[0], allLines[Math.floor(allLines.length / 2)]];
  }
  const n = parseInt(mode, 10);
  if (isNaN(n) || n < 1) return [allLines[0]];
  return allLines.slice(0, n);
}

// ─── HTML template ──────────────────────────────────────────────────────────

function pathToFileURL(filePath) {
  const absPath = resolve(filePath);
  if (process.platform === 'win32') {
    // Windows: C:\path\to\file → file:///C:/path/to/file
    return `file:///${absPath.replace(/\\/g, '/')}`;
  } else {
    // Unix: /path/to/file → file:///path/to/file
    return `file://${absPath}`;
  }
}

function generateHTML(meta, backgroundPath, selectedLines, width, height) {
  const title = meta.title || '无题';
  const dynasty = meta.dynasty || '';
  const author = meta.author || '';
  const subtitle = dynasty && author ? `${dynasty}·${author}` : (dynasty || author);

  const backgroundDataURL = `url('${pathToFileURL(backgroundPath)}')`;

  const fontFamily = FONT_PREFERENCES.join(', ');

  // Calculate font sizes based on canvas dimensions
  const titleFontSize = Math.floor(width * 0.055); // ~50px for 900px width
  const subtitleFontSize = Math.floor(width * 0.028); // ~25px
  const lineFontSize = Math.floor(width * 0.033); // ~30px

  const linesHTML = selectedLines.map(line =>
    `<div class="poem-line">${escapeHTML(line)}</div>`
  ).join('\n');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      width: ${width}px;
      height: ${height}px;
      background-image: ${backgroundDataURL};
      background-size: cover;
      background-position: center;
      font-family: ${fontFamily};
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      position: relative;
      overflow: hidden;
    }
    .text-overlay {
      text-align: center;
      color: white;
      text-shadow:
        0 2px 4px rgba(0,0,0,0.8),
        0 0 20px rgba(0,0,0,0.6);
      z-index: 10;
      padding: 0 40px;
      max-width: 90%;
    }
    .title {
      font-size: ${titleFontSize}px;
      font-weight: bold;
      margin-bottom: 10px;
      letter-spacing: 2px;
    }
    .subtitle {
      font-size: ${subtitleFontSize}px;
      margin-bottom: 30px;
      opacity: 0.95;
      letter-spacing: 1px;
    }
    .poem-lines {
      font-size: ${lineFontSize}px;
      line-height: 1.8;
      letter-spacing: 1px;
    }
    .poem-line {
      margin: 6px 0;
    }
  </style>
</head>
<body>
  <div class="text-overlay">
    <div class="title">${escapeHTML(title)}</div>
    ${subtitle ? `<div class="subtitle">${escapeHTML(subtitle)}</div>` : ''}
    ${linesHTML ? `<div class="poem-lines">${linesHTML}</div>` : ''}
  </div>
</body>
</html>`;
}

function escapeHTML(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const cfg = parseArgs();

  console.log('🎨 Cover Text Compositor');
  console.log(`📄 Meta: ${cfg.meta}`);
  console.log(`🖼️  Background: ${cfg.background}`);

  // 1. Load poem metadata
  const meta = JSON.parse(await readFile(cfg.meta, 'utf-8'));
  if (!meta.title || !meta.lines || meta.lines.length === 0) {
    throw new Error('poem-meta.json must have "title" and "lines" array');
  }

  // 2. Determine output dimensions
  const bgSize = await getImageSize(cfg.background);
  const width = cfg.width || bgSize.width;
  const height = cfg.height || bgSize.height;
  console.log(`📐 Output size: ${width}×${height}`);

  // 3. Select lines to display
  const selectedLines = cfg.titleOnly ? [] : selectLines(meta.lines, cfg.lines);
  console.log(`📝 Lines to display: ${selectedLines.length === 0 ? 'title only' : selectedLines.length === meta.lines.length ? 'full poem' : `${selectedLines.length} lines`}`);
  if (selectedLines.length > 0) {
    selectedLines.forEach((line, i) => console.log(`   ${i + 1}. ${line}`));
  }

  // 4. Generate HTML
  const html = generateHTML(meta, cfg.background, selectedLines, width, height);
  const hash = createHash('md5').update(html).digest('hex').slice(0, 8);
  const tmpHTML = resolve(tmpdir(), `cover-${hash}.html`);
  await writeFile(tmpHTML, html, 'utf-8');
  console.log(`📄 Temporary HTML: ${tmpHTML}`);

  // 5. Find Chrome
  const chromePath = await findChrome();
  console.log(`🌐 Chrome: ${basename(chromePath)}`);

  // 6. Render with Chrome headless
  console.log('🎬 Rendering...');
  const outputFormat = extname(cfg.output).toLowerCase() === '.png' ? 'png' : 'jpeg';
  const tmpScreenshot = resolve(tmpdir(), `screenshot-${hash}.png`);  // Chrome always outputs PNG

  await execCommand(chromePath, [
    '--headless',
    '--disable-gpu',
    '--disable-software-rasterizer',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    `--screenshot=${tmpScreenshot}`,
    `--window-size=${width},${height}`,
    `file://${tmpHTML}`,
  ]);

  // 7. Move to final output
  const screenshot = await readFile(tmpScreenshot);
  await writeFile(cfg.output, screenshot);
  console.log(`✅ Cover saved: ${cfg.output} (${(screenshot.length / 1024).toFixed(1)} KB)`);

  // 8. Verify text fields
  console.log('\n🔍 Verification checklist:');
  console.log(`   ✓ Title: ${meta.title}`);
  console.log(`   ✓ Dynasty: ${meta.dynasty}`);
  console.log(`   ✓ Author: ${meta.author}`);
  console.log(`   ✓ Lines: ${selectedLines.length} of ${meta.lines.length}`);
  console.log(`   ⚠️  Manual check: Open ${cfg.output} and verify text is readable and not cut off`);

  console.log(JSON.stringify({
    success: true,
    output: cfg.output,
    width,
    height,
    linesDisplayed: selectedLines.length,
    totalLines: meta.lines.length,
    bytes: screenshot.length,
  }));
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  console.log(JSON.stringify({ success: false, error: err.message }));
  process.exit(1);
});
