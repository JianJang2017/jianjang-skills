#!/bin/bash

# 发布功能集成验证脚本
# 验证 publish-to-wechat.js 脚本的所有功能

echo "=================================="
echo "发布功能集成验证"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
PASS=0
FAIL=0

echo "1. 检查发布脚本文件..."
echo "-----------------------------------"
if [ -f "scripts/publish-to-wechat.js" ]; then
    echo -e "${GREEN}✓${NC} scripts/publish-to-wechat.js 存在"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} scripts/publish-to-wechat.js 不存在"
    FAIL=$((FAIL + 1))
fi

if [ -x "scripts/publish-to-wechat.js" ]; then
    echo -e "${GREEN}✓${NC} scripts/publish-to-wechat.js 可执行"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} scripts/publish-to-wechat.js 不可执行"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "2. 检查依赖包..."
echo "-----------------------------------"
if [ -f "package.json" ]; then
    echo -e "${GREEN}✓${NC} package.json 存在"
    PASS=$((PASS + 1))

    if grep -q '"type": "module"' package.json; then
        echo -e "${GREEN}✓${NC} package.json 配置为 ES module"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} package.json 未配置为 ES module"
        FAIL=$((FAIL + 1))
    fi

    if grep -q '"marked"' package.json; then
        echo -e "${GREEN}✓${NC} marked 依赖已添加"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} 缺少 marked 依赖"
        FAIL=$((FAIL + 1))
    fi

    if grep -q '"form-data"' package.json; then
        echo -e "${GREEN}✓${NC} form-data 依赖已添加"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} 缺少 form-data 依赖"
        FAIL=$((FAIL + 1))
    fi
else
    echo -e "${RED}✗${NC} package.json 不存在"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "3. 检查配置文件..."
echo "-----------------------------------"
if [ -f ".env.example" ]; then
    echo -e "${GREEN}✓${NC} .env.example 存在"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} .env.example 不存在"
    FAIL=$((FAIL + 1))
fi

if [ -f ".gitignore" ]; then
    echo -e "${GREEN}✓${NC} .gitignore 存在"
    PASS=$((PASS + 1))

    if grep -q ".env" .gitignore; then
        echo -e "${GREEN}✓${NC} .gitignore 包含 .env"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗${NC} .gitignore 未包含 .env"
        FAIL=$((FAIL + 1))
    fi
else
    echo -e "${RED}✗${NC} .gitignore 不存在"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "4. 测试脚本功能..."
echo "-----------------------------------"

# 测试帮助信息
if node scripts/publish-to-wechat.js --help > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} --help 参数正常"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} --help 参数失败"
    FAIL=$((FAIL + 1))
fi

# 测试 dry-run 转换
if [ -f "evals/test-article.md" ]; then
    echo "  测试 Markdown → HTML 转换..."
    if node scripts/publish-to-wechat.js --article evals/test-article.md --dry-run --output /tmp/test-wechat-verify.html 2>&1 | grep -q "Dry-run 完成"; then
        echo -e "${GREEN}✓${NC} Markdown → HTML 转换成功"
        PASS=$((PASS + 1))

        if [ -f "/tmp/test-wechat-verify.html" ]; then
            echo -e "${GREEN}✓${NC} HTML 文件已生成"
            PASS=$((PASS + 1))

            # 检查 HTML 内容
            if grep -q "style=" /tmp/test-wechat-verify.html; then
                echo -e "${GREEN}✓${NC} HTML 包含样式"
                PASS=$((PASS + 1))
            else
                echo -e "${RED}✗${NC} HTML 未包含样式"
                FAIL=$((FAIL + 1))
            fi
        else
            echo -e "${RED}✗${NC} HTML 文件未生成"
            FAIL=$((FAIL + 1))
        fi
    else
        echo -e "${RED}✗${NC} Markdown → HTML 转换失败"
        FAIL=$((FAIL + 1))
    fi
else
    echo -e "${YELLOW}⚠${NC} 测试文章不存在，跳过转换测试"
fi
echo ""

echo "5. 检查 SKILL.md 更新..."
echo "-----------------------------------"
if grep -q "发布到公众号" SKILL.md; then
    echo -e "${GREEN}✓${NC} SKILL.md 包含发布功能"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} SKILL.md 未包含发布功能"
    FAIL=$((FAIL + 1))
fi

if grep -q "## 发布到微信公众号" SKILL.md; then
    echo -e "${GREEN}✓${NC} SKILL.md 包含发布章节"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} SKILL.md 未包含发布章节"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "6. 检查 npm scripts..."
echo "-----------------------------------"
if grep -q '"publish"' package.json; then
    echo -e "${GREEN}✓${NC} npm run publish 脚本已配置"
    PASS=$((PASS + 1))
else
    echo -e "${YELLOW}⚠${NC} npm run publish 脚本未配置"
fi
echo ""

echo "=================================="
echo "验证结果"
echo "=================================="
echo -e "通过: ${GREEN}$PASS${NC}"
echo -e "失败: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！发布功能已成功集成。${NC}"
    echo ""
    echo "下一步："
    echo "  1. 配置微信公众号凭证："
    echo "     cp .env.example ~/.config/wechat-mp/.env"
    echo "     编辑 ~/.config/wechat-mp/.env 填入真实凭证"
    echo ""
    echo "  2. 测试发布功能（需要凭证）："
    echo "     node scripts/publish-to-wechat.js --article evals/test-article.md --auto-cover"
    echo ""
    echo "  3. 或仅测试 HTML 转换（无需凭证）："
    echo "     node scripts/publish-to-wechat.js --article evals/test-article.md --dry-run"
    exit 0
else
    echo -e "${RED}✗ 发现 $FAIL 个问题，请检查上述失败项。${NC}"
    exit 1
fi
