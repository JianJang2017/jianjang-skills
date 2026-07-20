#!/usr/bin/env node

/**
 * 通义千问图像生成后端
 *
 * 支持通义千问（Qwen-Image）系列模型的图像生成
 * 文档：https://help.aliyun.com/zh/model-studio/text-to-image
 *
 * 功能特性：
 *  - 支持多种 Qwen 模型（qwen-image-2.0-pro, qwen-image-2.0, qwen-image-max, qwen-image-plus）
 *  - 支持自定义分辨率（512*512 至 2048*2048）
 *  - 支持 Prompt 智能改写
 *  - 支持负面提示词（negative_prompt）
 *  - 支持批量生成（1-6 张，仅 qwen-image-2.0 系列）
 *  - 自动从 .env 读取配置
 */

import { readFile, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import https from 'node:https';

// ─── 配置 ───────────────────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 地域端点映射
const REGION_ENDPOINTS = {
  'cn-beijing': {
    // 国内统一端点，无需 Workspace ID
    base: 'dashscope.aliyuncs.com',
    requiresWorkspace: false,
  },
  'ap-southeast-1': {
    // 新加坡地域需要 Workspace ID
    base: 'ap-southeast-1.maas.aliyuncs.com',
    requiresWorkspace: true,
  },
};

// 宽高比到分辨率的映射（针对不同模型系列）
const ASPECT_RATIO_MAP = {
  // qwen-image-2.0 系列（总像素 512*512 至 2048*2048）
  '2.0': {
    '16:9': '2688*1536',
    '9:16': '1536*2688',
    '1:1': '2048*2048',
    '4:3': '2368*1728',
    '3:4': '1728*2368',
  },
  // qwen-image-max / qwen-image-plus 系列
  'legacy': {
    '16:9': '1664*928',
    '9:16': '928*1664',
    '1:1': '1328*1328',
    '4:3': '1472*1104',
    '3:4': '1104*1472',
  },
};

// ─── 环境变量加载 ───────────────────────────────────────────────────────────

async function loadEnv() {
  const config = {
    apiKey: process.env.DASHSCOPE_API_KEY,
    workspaceId: process.env.DASHSCOPE_WORKSPACE_ID,
    region: process.env.DASHSCOPE_REGION || 'cn-beijing',
    model: process.env.QWEN_IMAGE_MODEL || 'qwen-image-2.0-pro-2026-04-22',
    promptExtend: (process.env.QWEN_PROMPT_EXTEND || 'true') === 'true',
    watermark: (process.env.QWEN_WATERMARK || 'false') === 'true',
    imageCount: parseInt(process.env.QWEN_IMAGE_COUNT || '1', 10),
  };

  // 尝试从项目 .env 文件加载（如果环境变量未设置）
  if (!config.apiKey || !config.workspaceId) {
    try {
      const envPath = resolve(__dirname, '..', '.env');
      const envContent = await readFile(envPath, 'utf-8');

      for (const line of envContent.split('\n')) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) continue;

        const [key, ...valueParts] = trimmed.split('=');
        const value = valueParts.join('=').replace(/^["']|["']$/g, '').trim();

        if (key === 'DASHSCOPE_API_KEY' && !config.apiKey) config.apiKey = value;
        if (key === 'DASHSCOPE_WORKSPACE_ID' && !config.workspaceId) config.workspaceId = value;
        if (key === 'DASHSCOPE_REGION' && !process.env.DASHSCOPE_REGION) config.region = value;
        if (key === 'QWEN_IMAGE_MODEL' && !process.env.QWEN_IMAGE_MODEL) config.model = value;
        if (key === 'QWEN_PROMPT_EXTEND' && !process.env.QWEN_PROMPT_EXTEND) {
          config.promptExtend = value === 'true';
        }
        if (key === 'QWEN_WATERMARK' && !process.env.QWEN_WATERMARK) {
          config.watermark = value === 'true';
        }
        if (key === 'QWEN_IMAGE_COUNT' && !process.env.QWEN_IMAGE_COUNT) {
          config.imageCount = parseInt(value, 10) || 1;
        }
      }
    } catch (err) {
      // .env 文件不存在时忽略
    }
  }

  return config;
}

// ─── HTTP 请求封装 ──────────────────────────────────────────────────────────

function httpsRequest(options, body = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve({ statusCode: res.statusCode, data: parsed });
        } catch (err) {
          resolve({ statusCode: res.statusCode, data });
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (body) req.write(typeof body === 'string' ? body : JSON.stringify(body));
    req.end();
  });
}

// ─── 通义千问图像生成 ───────────────────────────────────────────────────────

async function generateWithQwen(prompt, options = {}) {
  const config = await loadEnv();

  // 验证必需配置
  if (!config.apiKey) {
    throw new Error(
      '缺少 DASHSCOPE_API_KEY。请在 .env 文件中配置或设置环境变量。\n' +
      '获取方式：https://help.aliyun.com/zh/model-studio/get-api-key'
    );
  }

  // 检查地域配置
  const regionConfig = REGION_ENDPOINTS[config.region];
  if (!regionConfig) {
    throw new Error(`不支持的地域：${config.region}。支持：cn-beijing, ap-southeast-1`);
  }

  // 仅新加坡地域需要 Workspace ID
  if (regionConfig.requiresWorkspace && !config.workspaceId) {
    throw new Error(
      '新加坡地域（ap-southeast-1）需要 DASHSCOPE_WORKSPACE_ID。\n' +
      '获取方式：https://help.aliyun.com/zh/model-studio/obtain-the-app-id-and-workspace-id\n' +
      '提示：国内用户推荐使用 cn-beijing 地域，无需 Workspace ID'
    );
  }

  // 合并选项
  const model = options.model || config.model;
  const aspectRatio = options.aspectRatio || '1:1';
  const negativePrompt = options.negativePrompt || '';
  const promptExtend = options.promptExtend ?? config.promptExtend;
  const watermark = options.watermark ?? config.watermark;
  const imageCount = options.imageCount || config.imageCount;

  // 判断模型系列
  const is2Series = model.includes('2.0');
  const sizeMap = is2Series ? ASPECT_RATIO_MAP['2.0'] : ASPECT_RATIO_MAP['legacy'];
  const size = sizeMap[aspectRatio] || sizeMap['1:1'];

  // 构造请求体
  const requestBody = {
    model,
    input: {
      messages: [
        {
          role: 'user',
          content: [{ text: prompt }],
        },
      ],
    },
    parameters: {
      size,
      prompt_extend: promptExtend,
      watermark,
    },
  };

  // 添加负面提示词（如果提供）
  if (negativePrompt) {
    requestBody.parameters.negative_prompt = negativePrompt;
  }

  // 添加图片数量（仅 qwen-image-2.0 系列支持 1-6 张）
  if (is2Series && imageCount > 1 && imageCount <= 6) {
    requestBody.parameters.n = imageCount;
  }

  // 构造请求
  const endpoint = REGION_ENDPOINTS[config.region];
  if (!endpoint) {
    throw new Error(`不支持的地域：${config.region}。支持：cn-beijing, ap-southeast-1`);
  }

  // 构造主机名
  // 国内：直接使用统一端点
  // 新加坡：使用 Workspace ID 作为子域名
  const hostname = endpoint.requiresWorkspace && config.workspaceId
    ? `${config.workspaceId}.${endpoint.base}`
    : endpoint.base;

  const path = '/api/v1/services/aigc/multimodal-generation/generation';

  const requestOptions = {
    hostname,
    port: 443,
    path,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.apiKey}`,
    },
    timeout: options.timeout || 120000, // 默认 2 分钟超时
  };

  // 发送请求
  const response = await httpsRequest(requestOptions, requestBody);

  // 处理响应
  if (response.statusCode !== 200) {
    const errorMsg = response.data?.message || response.data || '未知错误';
    throw new Error(`通义千问 API 请求失败 (${response.statusCode}): ${errorMsg}`);
  }

  const result = response.data;

  // 检查返回结果
  if (result.code) {
    throw new Error(`通义千问 API 返回错误: ${result.code} - ${result.message}`);
  }

  if (!result.output?.choices?.[0]?.message?.content?.[0]?.image) {
    throw new Error('通义千问 API 返回数据格式异常：未找到图片 URL');
  }

  // 提取图片 URL
  const imageUrls = result.output.choices[0].message.content
    .filter(item => item.image)
    .map(item => item.image);

  if (imageUrls.length === 0) {
    throw new Error('通义千问 API 未返回任何图片');
  }

  return {
    urls: imageUrls,
    usage: result.usage,
    requestId: result.request_id,
    model,
    size,
  };
}

// ─── 下载图片 ───────────────────────────────────────────────────────────────

async function downloadImage(url, outputPath) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`图片下载失败: HTTP ${res.statusCode}`));
        return;
      }

      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', async () => {
        try {
          const buffer = Buffer.concat(chunks);
          await writeFile(outputPath, buffer);
          resolve(outputPath);
        } catch (err) {
          reject(err);
        }
      });
    }).on('error', reject);
  });
}

// ─── 命令行接口 ─────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
通义千问图像生成工具

用法:
  qwen-image-generator.js --prompt "<描述>" --output <路径> [选项]

必需参数:
  --prompt <文本>         图像描述提示词
  --output <路径>         输出图片路径

可选参数:
  --model <模型>          模型名称（默认: qwen-image-2.0-pro）
  --aspect-ratio <比例>   宽高比，如 16:9, 9:16, 1:1, 4:3, 3:4（默认: 1:1）
  --negative-prompt <文本> 负面提示词（描述不希望出现的内容）
  --prompt-extend         开启 Prompt 智能改写（默认开启）
  --no-prompt-extend      关闭 Prompt 智能改写
  --watermark             添加水印（默认不添加）
  --count <数量>          生成图片数量（1-6，仅 qwen-image-2.0 系列，默认: 1）
  --timeout <毫秒>        请求超时时间（默认: 120000）
  --help, -h              显示此帮助信息

环境变量（优先级高于 .env 文件）:
  DASHSCOPE_API_KEY       通义千问 API Key（必需）
  DASHSCOPE_WORKSPACE_ID  业务空间 ID（仅新加坡地域需要）
  DASHSCOPE_REGION        地域（cn-beijing | ap-southeast-1，默认: cn-beijing）
                          注意：国内地域（cn-beijing）无需 Workspace ID
  QWEN_IMAGE_MODEL        默认模型
  QWEN_PROMPT_EXTEND      默认是否开启 Prompt 改写（true | false）
  QWEN_WATERMARK          默认是否添加水印（true | false）
  QWEN_IMAGE_COUNT        默认图片数量（1-6）

支持的模型:
  qwen-image-2.0-pro      Pro 系列，文字渲染/真实质感更强（推荐）
  qwen-image-2.0          加速版，效果与性能平衡
  qwen-image-max          Max 系列，真实感与自然度更强
  qwen-image-plus         Plus 系列，多样化艺术风格

示例:
  # 生成单张图片
  node qwen-image-generator.js \\
    --prompt "一只坐着的橘黄色猫，表情愉悦" \\
    --output cat.png \\
    --aspect-ratio 1:1

  # 生成多张图片（qwen-image-2.0 系列）
  node qwen-image-generator.js \\
    --prompt "手绘风格的系统架构图" \\
    --output arch.png \\
    --count 3 \\
    --model qwen-image-2.0-pro

  # 使用负面提示词
  node qwen-image-generator.js \\
    --prompt "美丽的风景画" \\
    --negative-prompt "低分辨率，模糊，扭曲" \\
    --output landscape.png
`);
    process.exit(0);
  }

  // 解析参数
  const options = {
    prompt: null,
    output: null,
    model: null,
    aspectRatio: null,
    negativePrompt: null,
    promptExtend: null,
    watermark: null,
    imageCount: null,
    timeout: null,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '--prompt':
        options.prompt = args[++i];
        break;
      case '--output':
        options.output = args[++i];
        break;
      case '--model':
        options.model = args[++i];
        break;
      case '--aspect-ratio':
      case '--ar':
        options.aspectRatio = args[++i];
        break;
      case '--negative-prompt':
        options.negativePrompt = args[++i];
        break;
      case '--prompt-extend':
        options.promptExtend = true;
        break;
      case '--no-prompt-extend':
        options.promptExtend = false;
        break;
      case '--watermark':
        options.watermark = true;
        break;
      case '--count':
        options.imageCount = parseInt(args[++i], 10);
        break;
      case '--timeout':
        options.timeout = parseInt(args[++i], 10);
        break;
    }
  }

  if (!options.prompt || !options.output) {
    console.error('错误: 必须提供 --prompt 和 --output 参数');
    console.error('运行 --help 查看使用说明');
    process.exit(1);
  }

  try {
    console.log('🎨 正在通过通义千问生成图片...');

    // 生成图片
    const result = await generateWithQwen(options.prompt, options);

    console.log(`✅ 生成成功！共 ${result.urls.length} 张图片`);
    console.log(`   模型: ${result.model}`);
    console.log(`   分辨率: ${result.size}`);
    console.log(`   请求ID: ${result.requestId}`);

    // 下载图片
    const downloadedPaths = [];
    for (let i = 0; i < result.urls.length; i++) {
      const url = result.urls[i];
      const outputPath = result.urls.length > 1
        ? options.output.replace(/(\.[^.]+)$/, `-${i + 1}$1`)
        : options.output;

      console.log(`📥 正在下载图片 ${i + 1}/${result.urls.length}...`);
      await downloadImage(url, outputPath);
      downloadedPaths.push(outputPath);
      console.log(`   ✅ 已保存: ${outputPath}`);
    }

    // 输出机器可读的 JSON 结果（最后一行）
    console.log(JSON.stringify({
      success: true,
      count: downloadedPaths.length,
      outputs: downloadedPaths,
      usage: result.usage,
    }));

    process.exit(0);
  } catch (err) {
    console.error('❌ 生成失败:', err.message);
    console.log(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

// ─── 导出 ───────────────────────────────────────────────────────────────────

export { generateWithQwen, downloadImage, loadEnv };

// 如果直接运行（非导入）
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
