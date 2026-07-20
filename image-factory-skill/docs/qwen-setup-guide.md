# 通义千问（Qwen-Image）图像生成配置指南

本文档介绍如何配置和使用通义千问图像生成 API 作为 image-factory-skill 的生图后端。

## 目录

- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [使用方法](#使用方法)
- [高级功能](#高级功能)
- [故障排查](#故障排查)

---

## 快速开始

### 1. 获取 API Key

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 选择地域（华北2北京 或 新加坡）
3. 进入 **API Key 管理**
4. 点击 **创建新的 API Key**
5. 复制并保存 API Key（格式：`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

📖 详细说明：https://help.aliyun.com/zh/model-studio/get-api-key

**重要提示：**
- ⚠️ **国内地域（华北2北京）只需要 API Key，无需 Workspace ID**
- ⚠️ 新加坡地域需要 API Key 和 Workspace ID
- ⚠️ 不同地域的 API Key 不可混用

### 2. 配置 .env 文件

在 `image-factory-skill` 目录下编辑 `.env` 文件（没有则从 `.env.example` 复制）：

```bash
# 通义千问图像生成配置（国内用户）
DASHSCOPE_API_KEY=sk-your-actual-api-key-here
DASHSCOPE_REGION=cn-beijing
QWEN_IMAGE_MODEL=qwen-image-2.0-pro-2026-04-22

# 如果使用新加坡地域，还需要配置 Workspace ID
# DASHSCOPE_WORKSPACE_ID=ws-your-workspace-id-here
# DASHSCOPE_REGION=ap-southeast-1
```

**重要提示：**

- ⚠️ **国内地域（cn-beijing）只需要 API Key，无需 Workspace ID**
- ⚠️ 新加坡地域（ap-southeast-1）需要 API Key + Workspace ID
- ⚠️ 不同地域的 API Key 不可混用
- 💡 **国内用户推荐使用 cn-beijing，配置更简单，速度更快**

### 3. 测试生成

```bash
# 测试单独的 Qwen 生成器
node scripts/qwen-image-generator.js \
  --prompt "一只坐着的橘黄色猫，表情愉悦，活泼可爱" \
  --output test-cat.png

# 测试集成到 generate-image.js
node scripts/generate-image.js \
  --prompt-file test-prompt.md \
  --output test.png \
  --provider qwen

# 测试完整的飞书推送流程
python scripts/send_feishu_image.py \
  --prompt "手绘风格的系统架构图" \
  --provider qwen \
  --dry-run
```

---

## 配置说明

### 必需配置

| 环境变量 | 说明 | 示例值 | 备注 |
|---------|------|--------|------|
| `DASHSCOPE_API_KEY` | 通义千问 API Key | `sk-abc123...` | 必需 |
| `DASHSCOPE_WORKSPACE_ID` | 业务空间 ID | `ws-def456...` | 仅新加坡地域需要 |

**说明：**
- 🇨🇳 **国内地域（cn-beijing）**：只需要 `DASHSCOPE_API_KEY`
- 🌏 **新加坡地域（ap-southeast-1）**：需要 `DASHSCOPE_API_KEY` + `DASHSCOPE_WORKSPACE_ID`

### 可选配置

| 环境变量 | 说明 | 默认值 | 可选值 |
|---------|------|--------|--------|
| `DASHSCOPE_REGION` | 服务地域 | `cn-beijing` | `cn-beijing`, `ap-southeast-1` |
| `QWEN_IMAGE_MODEL` | 使用的模型 | `qwen-image-2.0-pro-2026-04-22` | 见下方模型对比 |
| `QWEN_PROMPT_EXTEND` | 是否智能改写提示词 | `true` | `true`, `false` |
| `QWEN_WATERMARK` | 是否添加水印 | `false` | `true`, `false` |
| `QWEN_IMAGE_COUNT` | 默认生成图片数量 | `1` | `1-6`（仅 2.0 系列）|

### 模型对比

| 模型 | 特点 | 适用场景 | 价格 |
|------|------|---------|------|
| `qwen-image-2.0-pro` ⭐ | Pro 系列，文字渲染/真实质感/语义遵循更强 | 需要高质量文字渲染、写实场景 | 较高 |
| `qwen-image-2.0` | 加速版，效果与性能平衡 | 日常使用，追求速度和质量平衡 | 中等 |
| `qwen-image-max` | 真实感与自然度更强，AI 痕迹更低 | 人物、自然场景、摄影风格 | 高 |
| `qwen-image-plus` | 多样化艺术风格与文字渲染 | 艺术创作、多样化风格 | 低 |

💡 **推荐：** 日常使用 `qwen-image-2.0-pro`，追求性价比用 `qwen-image-2.0`

---

## 使用方法

### 方法 1：直接使用 Qwen 生成器

```bash
# 基础用法
node scripts/qwen-image-generator.js \
  --prompt "一副典雅庄重的对联悬挂于厅堂之中" \
  --output output.png

# 指定宽高比
node scripts/qwen-image-generator.js \
  --prompt "赛博朋克风格的城市夜景" \
  --output cyberpunk.png \
  --aspect-ratio 16:9

# 使用负面提示词
node scripts/qwen-image-generator.js \
  --prompt "美丽的风景画" \
  --negative-prompt "低分辨率，模糊，扭曲，画面过饱和" \
  --output landscape.png

# 生成多张图片（qwen-image-2.0 系列）
node scripts/qwen-image-generator.js \
  --prompt "手绘风格的流程图" \
  --output diagram.png \
  --count 3 \
  --model qwen-image-2.0-pro
```

### 方法 2：通过 generate-image.js（推荐）

```bash
# 使用 qwen provider
node scripts/generate-image.js \
  --prompt-file prompts/20260720-01.md \
  --output result.png \
  --provider qwen

# 自动选择 provider（qwen 优先级最高）
node scripts/generate-image.js \
  --prompt-file prompts/my-prompt.md \
  --output result.png \
  --provider auto
```

### 方法 3：飞书推送集成

```bash
# 生成并发送到飞书
python scripts/send_feishu_image.py \
  --prompt "科技感的系统架构图" \
  --provider qwen \
  --user-ids "ou_xxx" \
  --caption "最新架构设计"

# 生成多张并发送
python scripts/send_feishu_image.py \
  --prompt "手绘风格的产品路线图" \
  --provider qwen \
  --count 3 \
  --chat-ids "oc_xxx"

# 预览模式（不实际发送）
python scripts/send_feishu_image.py \
  --prompt "测试图片" \
  --provider qwen \
  --dry-run
```

### 方法 4：小红书/抖音发布集成

```bash
# 生成并发布到小红书
node scripts/publish_xiaohongshu.js \
  --prompt "古风人物写真，雪中红衣女子回眸" \
  --provider qwen \
  --aspect-ratio 3:4 \
  --topics "AI,古风"

# 生成并发布到抖音
node scripts/publish_douyin.js \
  --prompt "赛博朋克风格的城市夜景" \
  --provider qwen \
  --topics "AI,夜景"
```

---

## 高级功能

### 1. Prompt 智能改写

通义千问支持智能改写 prompt，让图像内容更丰富：

```bash
# 开启智能改写（默认）
node scripts/qwen-image-generator.js \
  --prompt "一只猫" \
  --output cat.png \
  --prompt-extend

# 关闭智能改写（更可控）
node scripts/qwen-image-generator.js \
  --prompt "一只坐着的橘黄色猫，表情愉悦，活泼可爱，逼真准确" \
  --output cat.png \
  --no-prompt-extend
```

**什么时候关闭智能改写？**

- 需要精确控制图像细节
- 已经写好了详细的 prompt
- 想要多次生成相似的图像

### 2. 负面提示词（Negative Prompt）

描述不希望在图像中出现的内容：

```bash
node scripts/qwen-image-generator.js \
  --prompt "美丽的人物肖像" \
  --negative-prompt "低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感，构图混乱，文字模糊，扭曲" \
  --output portrait.png
```

**常用负面提示词模板：**

```
# 通用质量
低分辨率，低画质，模糊，扭曲，画面过饱和

# 人物相关
肢体畸形，手指畸形，蜡像感，人脸无细节，过度光滑，画面具有AI感

# 构图相关
构图混乱，杂乱无章

# 文字相关
文字模糊，文字扭曲，文字错误
```

### 3. 批量生成

通义千问 2.0 系列支持一次生成 1-6 张图片：

```bash
# 通过 qwen-image-generator
node scripts/qwen-image-generator.js \
  --prompt "手绘风格的架构图" \
  --output arch.png \
  --count 3 \
  --model qwen-image-2.0-pro
# 输出：arch-1.png, arch-2.png, arch-3.png

# 通过 generate-image.js
node scripts/generate-image.js \
  --prompt-file prompt.md \
  --output result.png \
  --count 3 \
  --provider qwen
# 输出：result-1.png, result-2.png, result-3.png
```

### 4. 支持的宽高比

#### qwen-image-2.0 系列

| 宽高比 | 分辨率 | 适用场景 |
|--------|--------|---------|
| `16:9` | 2688×1536 | 横版海报、PPT |
| `9:16` | 1536×2688 | 竖版海报、手机壁纸、社交媒体 |
| `1:1` | 2048×2048 | 正方形图标、社交媒体封面 |
| `4:3` | 2368×1728 | 传统横版 |
| `3:4` | 1728×2368 | 传统竖版 |

#### qwen-image-max / plus 系列

| 宽高比 | 分辨率 | 适用场景 |
|--------|--------|---------|
| `16:9` | 1664×928 | 横版 |
| `9:16` | 928×1664 | 竖版 |
| `1:1` | 1328×1328 | 正方形 |
| `4:3` | 1472×1104 | 横版 |
| `3:4` | 1104×1472 | 竖版 |

---

## 故障排查

### 问题 1：提示 "缺少 DASHSCOPE_API_KEY"

**原因：** 未配置 API Key 或配置文件路径不对

**解决：**

```bash
# 检查 .env 文件是否存在
ls -la .env

# 检查 API Key 是否配置
grep DASHSCOPE_API_KEY .env

# 或者直接设置环境变量
export DASHSCOPE_API_KEY="sk-your-key"
export DASHSCOPE_WORKSPACE_ID="ws-your-workspace"
```

### 问题 2：报错 "InvalidApiKey" 或鉴权失败

**原因：** API Key 不正确或与地域不匹配

**解决：**

1. 确认 API Key 格式正确（以 `sk-` 开头）
2. 确认 API Key 对应的地域与 `DASHSCOPE_REGION` 一致
3. 北京的 Key 不能用于新加坡，反之亦然

```bash
# 华北2（北京）
DASHSCOPE_REGION=cn-beijing

# 新加坡
DASHSCOPE_REGION=ap-southeast-1
```

### 问题 3：生成失败，提示 "RESOURCE_EXHAUSTED" 或配额不足

**原因：** API 配额用尽

**解决：**

1. 查看 [模型价格](https://help.aliyun.com/zh/model-studio/model-pricing) 了解计费
2. 访问 [百炼控制台](https://bailian.console.aliyun.com/) 查看配额使用情况
3. 申请提升配额或等待配额重置

### 问题 4：图片下载失败

**原因：** 网络问题或图片 URL 过期

**解决：**

1. 检查网络连接
2. 图片 URL 有效期为 24 小时，请及时下载
3. 如果下载失败，可以重新生成

### 问题 5：qwen provider 未被识别

**原因：** 配置未正确加载或模块导入失败

**解决：**

```bash
# 检查 qwen-image-generator.js 是否存在
ls -la scripts/qwen-image-generator.js

# 测试独立运行
node scripts/qwen-image-generator.js --help

# 检查 generate-image.js 是否最新
node scripts/generate-image.js --help | grep qwen
```

### 问题 6：Provider 优先级问题

**问题：** 设置了 `--provider auto`，但没有使用 Qwen

**原因：** 配置检测失败或 Qwen 配置不完整

**优先级顺序：** qwen > codex > gemini

**解决：**

```bash
# 显式指定 provider
node scripts/generate-image.js \
  --prompt-file prompt.md \
  --output result.png \
  --provider qwen

# 或者卸载其他 provider（如果只想用 Qwen）
# 不设置 codex 和 agy 的 PATH
```

---

## 性能和成本

### 性能对比

| 后端 | 平均耗时 | 并发能力 | 稳定性 |
|------|---------|---------|--------|
| Qwen API | 10-30 秒 | 高（API 限流） | ⭐⭐⭐⭐⭐ |
| Codex CLI | 30-120 秒 | 低（本地串行） | ⭐⭐⭐ |
| Gemini (agy) | 20-60 秒 | 中（API 限流） | ⭐⭐⭐⭐ |

### 成本估算

参考 [模型价格](https://help.aliyun.com/zh/model-studio/model-pricing#11a4ac6ea62wt)：

- **qwen-image-2.0-pro**：按成功生成的图像张数计费
- **qwen-image-2.0**：比 Pro 便宜约 30-50%
- **qwen-image-max**：与 Pro 价格相近
- **qwen-image-plus**：最便宜

💡 **省钱技巧：**

1. 日常测试用 `qwen-image-2.0` 或 `qwen-image-plus`
2. 正式产出用 `qwen-image-2.0-pro`
3. 利用批量生成（`--count`）减少重复调用
4. 合理使用负面提示词，提高首次成功率

---

## 扩展阅读

- [通义千问图像生成 API 文档](https://help.aliyun.com/zh/model-studio/text-to-image)
- [获取 API Key](https://help.aliyun.com/zh/model-studio/get-api-key)
- [获取 Workspace ID](https://help.aliyun.com/zh/model-studio/obtain-the-app-id-and-workspace-id)
- [模型价格](https://help.aliyun.com/zh/model-studio/model-pricing)
- [错误码](https://help.aliyun.com/zh/model-studio/error-code)
- [文生图 Prompt 指南](https://help.aliyun.com/zh/model-studio/text-to-image-prompt)

---

## 反馈与支持

遇到问题？

1. 查看本文档的 [故障排查](#故障排查) 部分
2. 查看 [通义千问错误码文档](https://help.aliyun.com/zh/model-studio/error-code)
3. 提交 Issue 到项目仓库

---

**最后更新：** 2026-07-20
