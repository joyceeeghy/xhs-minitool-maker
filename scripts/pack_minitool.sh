#!/bin/bash
# 小红书小工具打包脚本：从 minitool 目录内打包（index.html 必须在 zip 根级）
# 用法: bash pack_minitool.sh <minitool目录> <输出zip路径>
set -e
SRC="${1:?用法: pack_minitool.sh <minitool目录> <输出zip>}"
OUT="${2:?缺少输出 zip 路径}"
find "$SRC" -name .DS_Store -delete 2>/dev/null || true
mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
rm -f "$OUT"
( cd "$SRC" && zip -qr "$OUT" . -x "*.DS_Store" )
SIZE=$(stat -f%z "$OUT")
FILES=$(unzip -l "$OUT" | tail -1 | awk '{print $2}')
echo "打包完成: $OUT"
echo "大小: $((SIZE/1024/1024)).$(( (SIZE/1024%1024)*10/1024 ))MB / 文件数: $FILES"
if [ "$SIZE" -gt 31457280 ]; then
  echo "⚠️ 超过小红书 30MB 限制，请压缩资源（贴图/模型/图片）后重试" >&2
  exit 1
fi
