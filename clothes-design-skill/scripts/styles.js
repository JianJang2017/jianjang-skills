/**
 * styles.js — 共享风格预设库
 *
 * reverse-prompt.js / optimize-prompt.js / generate-portrait-prompt.js 共用这一份。
 *
 * 「扩展风格」= 往 STYLE_PRESETS 加一条。每条字段：
 *   label     中文名（给人看）
 *   zh        中文风格描述（写进后端 prompt，让它读）
 *   keywords  英文修饰词组（让后端融入 [Style] / [Key elements] 段）
 *   kind      'general'（通用，可用于 optimize 任意题材）
 *             | 'portrait'（人物写真专用，generate-portrait-prompt 默认只列这些）
 *   portrait  仅 kind==='portrait' 时给：人物图的额外拍摄指引
 *             { camera, lighting, composition, quality, negative }
 *
 * 设计意图：把"风格"沉淀成数据而非散落在各脚本里的字符串，这样三个脚本行为一致，
 * 加新风格只改这一个文件，不会出现"optimize 认识某风格但 portrait 不认识"的漂移。
 */

export const STYLE_PRESETS = {
  // ─── 人物写真类 (kind: portrait) ──────────────────────────────────────────
  // gufeng-portrait 从 images/ 下四张「古代女子妆容」海报反推提炼而来：
  // warm cream 宣纸底、金色细线质感、柔焦棚拍、汉服盘发珠钗、清透古风妆。
  // 注意：原图是四宫格 infographic 合集，这个预设刻意只取"单人写真"那一层，
  // 去掉标题/编号/排版，专注把一个古风人物拍好看。
  'gufeng-portrait': {
    label: '古风宫廷写真',
    kind: 'portrait',
    zh: '古典中式古风宫廷人物写真，warm cream 米白背景，金色细节质感，柔焦棚拍摄影，雅致留白',
    keywords:
      'classical Chinese gufeng portrait, warm cream background, soft-focus studio photography, ' +
      'hanfu costume, ornate updo hairstyle with pearl and gold hairpins, hair ornaments, ' +
      'delicate traditional makeup (sheer base, peach-pink eyeshadow, soft brows, red lips, floral huadian forehead mark), ' +
      'elegant, refined, warm golden light',
    portrait: {
      camera: '半身或胸像特写，浅景深，85mm 人像镜头视角',
      lighting: '柔和棚拍光 / golden hour warm light，高光柔过渡，肤质通透',
      composition: '人物居中或三分构图，warm cream / 宣纸质感背景，留白雅致，可带细金线点缀',
      quality: '高细节、精致皮肤质感、清晰五官、photorealistic、masterpiece、best quality',
      negative: '避免：四宫格/拼图排版、标题文字、编号圆章、水印、UI、多余文字、低分辨率、变形手部',
    },
  },

  'photo-portrait': {
    label: '写实人像摄影',
    kind: 'portrait',
    zh: '写实人像摄影风，自然光，真实皮肤质感，电影感',
    keywords:
      'photorealistic portrait, natural light, true-to-life skin texture, cinematic, 35mm look, shallow depth of field',
    portrait: {
      camera: '半身或环境人像，浅景深，35mm / 85mm',
      lighting: '自然光 / 柔和窗光，真实光影',
      composition: '三分构图，背景虚化，环境点题',
      quality: '高细节、真实肤质、masterpiece、best quality、8k',
      negative: '避免：插画感、塑料皮肤、过度磨皮、水印、UI、变形手部、低分辨率',
    },
  },

  // ─── 通用类 (kind: general) ───────────────────────────────────────────────
  'hand-drawn': {
    label: '手绘风',
    kind: 'general',
    zh: '手绘风格、warm cream 背景、黑色线条、pastel 色块',
    keywords: 'hand-drawn, warm cream background, black ink lines, pastel color blocks, sketchy texture',
  },
  blueprint: {
    label: '科技蓝图',
    kind: 'general',
    zh: '科技蓝图风、blueprint grid 背景、白色线稿、淡蓝色调',
    keywords: 'blueprint style, grid background, white wireframe lines, technical schematic, cyan tone',
  },
  watercolor: {
    label: '水彩',
    kind: 'general',
    zh: '水彩风、柔光、纸纹、淡雅配色',
    keywords: 'watercolor painting, soft light, paper texture, muted palette, ink bleed',
  },
  cyberpunk: {
    label: '赛博朋克',
    kind: 'general',
    zh: '赛博朋克风、霓虹灯、雨夜街景、高对比',
    keywords: 'cyberpunk style, neon lights, rainy night, high contrast, magenta + cyan',
  },
  '3d': {
    label: '3D 渲染',
    kind: 'general',
    zh: '3D 渲染、柔光、景深、materials 写实',
    keywords: '3D render, soft lighting, depth of field, realistic materials, octane render look',
  },
  healing: {
    label: '治愈系',
    kind: 'general',
    zh: '治愈系、柔色、低饱和、暖色基调',
    keywords: 'healing aesthetic, soft palette, low saturation, warm tone, cozy mood',
  },
  minimal: {
    label: '极简',
    kind: 'general',
    zh: '极简风、大量留白、大字号、克制配色',
    keywords: 'minimalist, generous whitespace, oversized typography, restrained palette, geometric',
  },
  photo: {
    label: '摄影风',
    kind: 'general',
    zh: '摄影风、自然光、真实质感、电影感',
    keywords: 'photorealistic, natural light, true-to-life texture, cinematic, 35mm look',
  },

  // ─── 元预设 ──────────────────────────────────────────────────────────────
  keep: {
    label: '保留原风格',
    kind: 'general',
    zh: '保留原 prompt 的视觉风格，仅做结构化和措辞润色',
    keywords: '(keep the original visual style; only restructure and polish the wording)',
  },
  auto: {
    label: '自动判断',
    kind: 'general',
    zh: '由后端按原 prompt 的语境自行判断最合适的风格',
    keywords: '(infer the most appropriate visual style from the original prompt context)',
  },
};

/** 列出所有风格（可按 kind 过滤）。返回 [{key, label, zh, kind}] */
export function listStyles(kind = null) {
  return Object.entries(STYLE_PRESETS)
    .filter(([, v]) => !kind || v.kind === kind || v.key === 'keep' || v.key === 'auto')
    .map(([key, v]) => ({ key, label: v.label || key, zh: v.zh, kind: v.kind || 'general' }));
}

/** 取一个预设，找不到返回 null */
export function getStyle(key) {
  return STYLE_PRESETS[key] || null;
}

/** 格式化成 --list-styles 的可读文本 */
export function formatStyleList(kind = null) {
  const rows = Object.entries(STYLE_PRESETS).filter(([, v]) => {
    if (!kind) return true;
    return v.kind === kind;
  });
  const lines = rows.map(([key, v]) => `  ${key.padEnd(16)}${v.label || ''}  —  ${v.zh}`);
  return lines.join('\n');
}
