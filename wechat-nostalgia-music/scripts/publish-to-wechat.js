#!/usr/bin/env node

/**
 * WeChat Official Account Publisher
 *
 * 功能：将 Markdown 文章转换为 HTML 并发布到微信公众号草稿箱
 *
 * 流程：
 * 1. Markdown → HTML 转换
 * 2. 上传图片素材（封面图 + 正文图片）
 * 3. 替换图片为微信 media_id
 * 4. 创建草稿（包含标题、作者、内容、封面等）
 *
 * 使用：
 *   node publish-to-wechat.js --article article.md --cover cover.jpg
 *   node publish-to-wechat.js --article article.md --auto-cover (自动使用第一张图作为封面)
 */

import { readFile, writeFile, stat } from 'node:fs/promises';
import { resolve, dirname, basename, extname, join } from 'node:path';
import { spawn } from 'node:child_process';
import { marked } from 'marked';

// ─── 配置 ─────────────────────────────────────────────────────────────────

const CONFIG = {
  // 从环境变量或配置文件读取
  appId: process.env.WECHAT_APP_ID || '',
  appSecret: process.env.WECHAT_APP_SECRET || '',

  // API 端点
  tokenUrl: 'https://api.weixin.qq.com/cgi-bin/token',
  uploadUrl: 'https://api.weixin.qq.com/cgi-bin/material/add_material',
  draftUrl: 'https://api.weixin.qq.com/cgi-bin/draft/add',

  // 默认值
  author: '怀旧音乐',
  defaultCoverType: '2.35:1', // 宽封面
};

// ─── 参数解析 ─────────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    article: null,
    cover: null,
    autoCover: false,
    author: CONFIG.author,
    digest: null, // 摘要
    showCoverPic: 1, // 是否显示封面，0不显示 1显示
    needOpenComment: 0, // 是否打开评论，0不打开 1打开
    onlyFansCanComment: 0, // 是否粉丝才可评论，0所有人可评论 1粉丝才可评论
    output: null, // 输出 HTML 路径
    dryRun: false, // 仅转换 HTML，不发布
  };

  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    switch (a) {
      case '--article': case '-a': cfg.article = args[++i]; break;
      case '--cover': case '-c': cfg.cover = args[++i]; break;
      case '--auto-cover': cfg.autoCover = true; break;
      case '--author': cfg.author = args[++i]; break;
      case '--digest': cfg.digest = args[++i]; break;
      case '--no-cover': cfg.showCoverPic = 0; break;
      case '--open-comment': cfg.needOpenComment = 1; break;
      case '--fans-only-comment': cfg.onlyFansCanComment = 1; break;
      case '--output': case '-o': cfg.output = args[++i]; break;
      case '--dry-run': cfg.dryRun = true; break;
      case '--help': case '-h': showHelp(); process.exit(0);
      default:
        if (!cfg.article && !a.startsWith('-')) cfg.article = a;
    }
  }

  if (!cfg.article) {
    console.error('错误: 缺少 --article 参数');
    showHelp();
    process.exit(1);
  }

  return cfg;
}

function showHelp() {
  console.log(`
用法:
  publish-to-wechat.js --article <article.md> [options]

选项:
  --article, -a <path>        Markdown 文章路径 (必需)
  --cover, -c <path>          封面图片路径
  --auto-cover                自动使用第一张图作为封面
  --author <name>             作者名称 (默认: ${CONFIG.author})
  --digest <text>             文章摘要（不超过120字）
  --no-cover                  不显示封面图
  --open-comment              打开评论功能
  --fans-only-comment         仅粉丝可评论
  --output, -o <path>         输出 HTML 文件路径
  --dry-run                   仅转换 HTML，不发布到微信
  --help, -h                  显示此帮助信息

环境变量:
  WECHAT_APP_ID               微信公众号 AppID
  WECHAT_APP_SECRET           微信公众号 AppSecret

配置文件:
  ~/.config/wechat-mp/.env    可选的配置文件

示例:
  # 发布文章，指定封面
  publish-to-wechat.js --article article.md --cover cover.jpg

  # 发布文章，自动使用第一张图作为封面
  publish-to-wechat.js --article article.md --auto-cover

  # 仅生成 HTML，不发布
  publish-to-wechat.js --article article.md --dry-run --output article.html

  # 打开评论，粉丝可评论
  publish-to-wechat.js --article article.md --cover cover.jpg --open-comment --fans-only-comment
`);
}

// ─── 工具函数 ─────────────────────────────────────────────────────────────

async function exists(path) {
  try { await stat(path); return true; } catch { return false; }
}

async function httpRequest(url, options = {}) {
  const https = await import('node:https');

  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (json.errcode && json.errcode !== 0) {
            reject(new Error(`API Error ${json.errcode}: ${json.errmsg}`));
          } else {
            resolve(json);
          }
        } catch (e) {
          resolve(data);
        }
      });
    });

    req.on('error', reject);

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

async function uploadFile(url, filePath, type = 'image') {
  const FormData = (await import('form-data')).default;
  const form = new FormData();

  const fileBuffer = await readFile(filePath);
  form.append('media', fileBuffer, {
    filename: basename(filePath),
    contentType: `${type}/${extname(filePath).slice(1)}`,
  });

  return new Promise((resolve, reject) => {
    form.submit(url, (err, res) => {
      if (err) return reject(err);

      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (json.errcode && json.errcode !== 0) {
            reject(new Error(`Upload failed ${json.errcode}: ${json.errmsg}`));
          } else {
            resolve(json);
          }
        } catch (e) {
          reject(new Error(`Failed to parse response: ${data}`));
        }
      });
    });
  });
}

// ─── 微信 API ──────────────────────────────────────────────────────────────

async function getAccessToken(appId, appSecret) {
  const url = `${CONFIG.tokenUrl}?grant_type=client_credential&appid=${appId}&secret=${appSecret}`;
  const result = await httpRequest(url);

  if (!result.access_token) {
    throw new Error('Failed to get access token');
  }

  console.log('✓ 获取 access_token 成功');
  return result.access_token;
}

async function uploadMaterial(accessToken, filePath, type = 'image') {
  const url = `${CONFIG.uploadUrl}?access_token=${accessToken}&type=${type}`;
  console.log(`  上传素材: ${basename(filePath)}`);

  const result = await uploadFile(url, filePath, type);

  if (!result.media_id) {
    throw new Error(`Upload failed: no media_id returned`);
  }

  console.log(`  ✓ media_id: ${result.media_id}`);
  return result.media_id;
}

async function createDraft(accessToken, article) {
  const url = `${CONFIG.draftUrl}?access_token=${accessToken}`;

  const body = JSON.stringify({
    articles: [article]
  });

  const result = await httpRequest(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body),
    },
    body,
  });

  if (!result.media_id) {
    throw new Error('Failed to create draft: no media_id returned');
  }

  console.log('✓ 草稿创建成功');
  console.log(`  media_id: ${result.media_id}`);
  return result.media_id;
}

// ─── Markdown → HTML ───────────────────────────────────────────────────────

function convertMarkdownToHTML(markdown) {
  // 配置 marked
  marked.setOptions({
    breaks: true, // 支持 GFM 换行
    gfm: true,
  });

  // 转换
  const content = marked.parse(markdown);

  // 添加微信公众号适配的样式
  const styledHTML = `
<section style="font-size: 16px; color: #333; line-height: 1.8; word-wrap: break-word; word-break: break-word;">
${content}
</section>
  `.trim();

  return styledHTML;
}

function applyWechatStyles(html) {
  // 为不同元素添加微信公众号友好的样式
  return html
    // 段落
    .replace(/<p>/g, '<p style="margin: 1em 0; text-align: justify;">')
    // 标题
    .replace(/<h1>/g, '<h1 style="font-size: 1.6em; font-weight: bold; margin: 1.2em 0 0.8em; line-height: 1.4;">')
    .replace(/<h2>/g, '<h2 style="font-size: 1.4em; font-weight: bold; margin: 1.2em 0 0.8em; line-height: 1.4;">')
    .replace(/<h3>/g, '<h3 style="font-size: 1.2em; font-weight: bold; margin: 1em 0 0.6em; line-height: 1.4;">')
    // 图片
    .replace(/<img /g, '<img style="max-width: 100%; height: auto; display: block; margin: 1em auto;" ')
    // 引用
    .replace(/<blockquote>/g, '<blockquote style="margin: 1em 0; padding: 0.5em 1em; border-left: 4px solid #ddd; color: #666; background: #f9f9f9;">')
    // 列表
    .replace(/<ul>/g, '<ul style="margin: 1em 0; padding-left: 2em;">')
    .replace(/<ol>/g, '<ol style="margin: 1em 0; padding-left: 2em;">')
    .replace(/<li>/g, '<li style="margin: 0.5em 0;">');
}

// ─── 图片处理 ─────────────────────────────────────────────────────────────

function extractImages(markdown, articleDir) {
  // 提取所有图片路径
  const imgRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  const images = [];
  let match;

  while ((match = imgRegex.exec(markdown)) !== null) {
    const alt = match[1];
    const src = match[2];

    // 转换为绝对路径
    const absolutePath = src.startsWith('/') || src.startsWith('http')
      ? src
      : resolve(articleDir, src);

    images.push({ alt, src, absolutePath });
  }

  return images;
}

async function uploadImages(accessToken, images) {
  const uploaded = [];

  console.log(`\n📤 上传图片素材 (${images.length} 张)...`);

  for (const img of images) {
    if (img.absolutePath.startsWith('http')) {
      console.log(`  跳过远程图片: ${img.src}`);
      uploaded.push({ ...img, mediaId: null, url: img.src });
      continue;
    }

    if (!(await exists(img.absolutePath))) {
      console.log(`  ⚠️  图片不存在: ${img.absolutePath}`);
      uploaded.push({ ...img, mediaId: null, url: img.src });
      continue;
    }

    try {
      const mediaId = await uploadMaterial(accessToken, img.absolutePath, 'image');
      uploaded.push({ ...img, mediaId });
    } catch (err) {
      console.error(`  ✗ 上传失败: ${img.absolutePath}`);
      console.error(`    ${err.message}`);
      uploaded.push({ ...img, mediaId: null, url: img.src });
    }
  }

  return uploaded;
}

function replaceImagesWithMediaId(html, uploadedImages) {
  let result = html;

  for (const img of uploadedImages) {
    if (!img.mediaId) continue;

    // 替换为微信 CDN 地址（微信会自动处理 media_id）
    const oldPattern = new RegExp(`<img ([^>]*)src="${img.src.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}"`, 'g');
    const newImg = `<img $1src="weixin://media_id/${img.mediaId}"`;
    result = result.replace(oldPattern, newImg);
  }

  return result;
}

// ─── 封面处理 ─────────────────────────────────────────────────────────────

async function handleCover(cfg, uploadedImages, accessToken) {
  let thumbMediaId = null;

  if (cfg.cover) {
    // 使用指定的封面
    console.log(`\n📷 上传封面图: ${cfg.cover}`);
    if (!(await exists(cfg.cover))) {
      throw new Error(`封面图不存在: ${cfg.cover}`);
    }
    thumbMediaId = await uploadMaterial(accessToken, cfg.cover, 'thumb');
  } else if (cfg.autoCover && uploadedImages.length > 0) {
    // 使用第一张图作为封面
    const firstImg = uploadedImages[0];
    if (firstImg.mediaId) {
      console.log(`\n📷 使用第一张图作为封面: ${firstImg.src}`);
      thumbMediaId = firstImg.mediaId;
    } else if (firstImg.absolutePath && !(firstImg.absolutePath.startsWith('http'))) {
      console.log(`\n📷 上传第一张图作为封面: ${firstImg.absolutePath}`);
      thumbMediaId = await uploadMaterial(accessToken, firstImg.absolutePath, 'thumb');
    }
  }

  return thumbMediaId;
}

// ─── 主流程 ───────────────────────────────────────────────────────────────

async function main() {
  const cfg = parseArgs();

  console.log('🎵 怀旧音乐公众号发布工具\n');
  console.log(`📄 文章: ${cfg.article}`);

  // 1. 读取 Markdown
  const articlePath = resolve(cfg.article);
  if (!(await exists(articlePath))) {
    throw new Error(`文章不存在: ${articlePath}`);
  }

  const markdown = await readFile(articlePath, 'utf-8');
  const articleDir = dirname(articlePath);

  // 2. 提取标题和内容
  const lines = markdown.split('\n');
  let title = basename(articlePath, '.md');
  let content = markdown;

  // 尝试从第一行提取标题
  if (lines[0].startsWith('# ')) {
    title = lines[0].replace(/^#\s+/, '').trim();
    content = lines.slice(1).join('\n').trim();
  }

  console.log(`📋 标题: ${title}`);

  // 3. 提取图片
  const images = extractImages(markdown, articleDir);
  console.log(`🖼️  发现 ${images.length} 张图片`);

  // 4. 转换 Markdown → HTML
  console.log('\n🔄 转换 Markdown → HTML...');
  let html = convertMarkdownToHTML(content);
  html = applyWechatStyles(html);

  // 如果是 dry-run，保存 HTML 并退出
  if (cfg.dryRun) {
    const outputPath = cfg.output || articlePath.replace(/\.md$/, '.html');
    await writeFile(outputPath, html, 'utf-8');
    console.log(`✓ HTML 已保存到: ${outputPath}`);
    console.log('\n🏁 Dry-run 完成，未发布到微信');
    return;
  }

  // 5. 检查凭证
  if (!CONFIG.appId || !CONFIG.appSecret) {
    throw new Error('缺少微信公众号凭证。请设置环境变量 WECHAT_APP_ID 和 WECHAT_APP_SECRET');
  }

  // 6. 获取 access_token
  console.log('\n🔐 获取 access_token...');
  const accessToken = await getAccessToken(CONFIG.appId, CONFIG.appSecret);

  // 7. 上传图片素材
  const uploadedImages = await uploadImages(accessToken, images);

  // 8. 替换图片为 media_id
  if (uploadedImages.some(img => img.mediaId)) {
    console.log('\n🔄 替换图片为微信素材...');
    html = replaceImagesWithMediaId(html, uploadedImages);
  }

  // 9. 处理封面
  const thumbMediaId = await handleCover(cfg, uploadedImages, accessToken);

  // 10. 生成摘要（如果未指定）
  let digest = cfg.digest;
  if (!digest) {
    // 从内容中提取前120字作为摘要
    const plainText = content
      .replace(/#{1,6}\s+/g, '') // 移除标题标记
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '') // 移除图片
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1') // 保留链接文字
      .replace(/[*_~`]/g, '') // 移除格式标记
      .trim();
    digest = plainText.slice(0, 120);
  }

  // 11. 创建草稿
  console.log('\n📝 创建草稿...');
  const article = {
    title,
    author: cfg.author,
    digest,
    content: html,
    content_source_url: '', // 原文链接，可选
    thumb_media_id: thumbMediaId || '',
    need_open_comment: cfg.needOpenComment,
    only_fans_can_comment: cfg.onlyFansCanComment,
    show_cover_pic: cfg.showCoverPic,
  };

  const draftMediaId = await createDraft(accessToken, article);

  // 12. 完成
  console.log('\n✅ 发布完成！');
  console.log(`\n📋 草稿信息:`);
  console.log(`  标题: ${title}`);
  console.log(`  作者: ${cfg.author}`);
  console.log(`  摘要: ${digest}`);
  console.log(`  封面: ${thumbMediaId ? '已上传' : '无'}`);
  console.log(`  图片: ${uploadedImages.filter(i => i.mediaId).length}/${images.length} 张已上传`);
  console.log(`  草稿 ID: ${draftMediaId}`);
  console.log(`\n💡 请登录微信公众号后台查看草稿箱`);
}

// ─── 入口 ─────────────────────────────────────────────────────────────────

main().catch(err => {
  console.error('\n❌ 错误:', err.message);
  if (err.stack) {
    console.error(err.stack);
  }
  process.exit(1);
});
