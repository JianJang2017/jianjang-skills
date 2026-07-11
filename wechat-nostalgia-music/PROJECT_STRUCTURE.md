# wechat-nostalgia-music 项目结构

## 目录树

```
wechat-nostalgia-music/
├── SKILL.md                          # 主技能文档 (1,073行)
├── README.md                         # 使用说明文档 (675行)
├── package.json                      # Node.js 依赖配置
├── package-lock.json                 # 依赖版本锁定
│
├── .env.example                      # 微信凭证配置示例
├── .gitignore                        # Git 忽略规则
│
├── scripts/                          # 可执行脚本目录
│   ├── generate-image.js             # 配图生成脚本 (455行)
│   ├── publish-to-wechat.js          # 发布脚本 (503行)
│   ├── verify-integration.sh         # 配图功能验证脚本
│   └── verify-publish.sh             # 发布功能验证脚本
│
├── references/                       # 参考文档目录
│   ├── compliance.md                 # 版权合规指南 (28行)
│   └── illustration-guide.md         # 配图详细指南 (457行)
│
├── evals/                            # 测试资源目录
│   ├── evals.json                    # 测试用例配置
│   └── test-article.md               # 测试文章
│
├── COMPLETION_SUMMARY.md             # 配图功能完成报告
├── INTEGRATION_REPORT.md             # 配图功能集成报告
├── PUBLISH_COMPLETION_REPORT.md      # 发布功能完成报告
└── FINAL_SUMMARY.md                  # 最终总结报告
```

## 文件说明

### 核心文档
- **SKILL.md**: 完整技能文档，包含所有创作规则、配图流程和发布流程
- **README.md**: 快速开始指南和功能概览

### 配置文件
- **package.json**: Node.js 项目配置，包含依赖和 npm scripts
- **.env.example**: 微信公众号凭证配置示例
- **.gitignore**: Git 版本控制忽略规则

### 脚本目录 (scripts/)
所有可执行脚本统一放置在此目录：

1. **generate-image.js**: 图片生成脚本
   - 支持 codex-cli 和 agy 双后端
   - 批量生成功能
   - 自动重试机制

2. **publish-to-wechat.js**: 发布脚本
   - Markdown → HTML 转换
   - 图片素材上传
   - 草稿箱管理

3. **verify-integration.sh**: 配图功能验证
   - 检查 21 项核心内容
   - 验证配图功能完整性

4. **verify-publish.sh**: 发布功能验证
   - 检查 16 项核心内容
   - 验证发布功能完整性

### 参考文档 (references/)
- **compliance.md**: 版权合规详细指南
- **illustration-guide.md**: 配图视觉风格和提示词模板

### 测试资源 (evals/)
- **evals.json**: 测试用例配置文件
- **test-article.md**: 测试文章示例

### 报告文档
- **COMPLETION_SUMMARY.md**: 配图功能完成总结
- **INTEGRATION_REPORT.md**: 配图功能集成详情
- **PUBLISH_COMPLETION_REPORT.md**: 发布功能完成总结
- **FINAL_SUMMARY.md**: 项目最终总结

## 使用的 npm scripts

```json
{
  "scripts": {
    "publish": "node scripts/publish-to-wechat.js",
    "generate-image": "node scripts/generate-image.js",
    "verify": "bash scripts/verify-integration.sh && bash scripts/verify-publish.sh",
    "verify:illustration": "bash scripts/verify-integration.sh",
    "verify:publish": "bash scripts/verify-publish.sh"
  }
}
```

## 快速命令

```bash
# 验证所有功能
npm run verify

# 仅验证配图功能
npm run verify:illustration

# 仅验证发布功能
npm run verify:publish

# 生成图片
npm run generate-image -- --prompt-file prompt.md --output img.png

# 发布文章
npm run publish -- --article article.md --auto-cover
```

## 依赖说明

### 运行时依赖
- **marked**: Markdown 解析和转换
- **form-data**: 文件上传（图片素材）

### 可选依赖
- **codex-cli**: OpenAI Codex 图片生成后端
- **agy**: Google Gemini 图片生成后端

### 外部服务
- **微信公众平台 API**: 需要配置 AppID 和 AppSecret

## 版本历史

- **v1.0.0**: 内容创作功能
- **v1.1.0**: 配图功能集成
- **v1.2.0**: 发布功能集成 (当前版本)

---

**最后更新**: 2026-07-10  
**当前版本**: v1.2.0  
**状态**: 生产就绪 ✅
