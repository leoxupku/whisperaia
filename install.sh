#!/bin/bash
set -euo pipefail

APP_NAME="WhisperAIA"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/Applications/$APP_NAME"
APP_BUNDLE="$HOME/Applications/$APP_NAME.app"

SYSTEM_ICON="/System/Library/Input Methods/DictationIM.app/Contents/Resources/Speech.icns"

echo "=== WhisperAIA 安装程序 ==="
echo ""

# ── 1. 复制项目文件 ────────────────────────────────────────────────────────────
if [ "$SCRIPT_DIR" = "$INSTALL_DIR" ]; then
    echo "→ 项目已在 $INSTALL_DIR，跳过复制"
else
    echo "→ 复制项目到 $INSTALL_DIR ..."
    mkdir -p "$HOME/Applications"
    rsync -a --delete \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.claude' \
        "$SCRIPT_DIR/" "$INSTALL_DIR/"
fi

# ── 2. 安装 Python 依赖（如果 venv 不存在）─────────────────────────────────────
if [ ! -f "$INSTALL_DIR/.venv/bin/python" ]; then
    echo "→ 创建虚拟环境并安装依赖..."
    python3 -m venv "$INSTALL_DIR/.venv"
    "$INSTALL_DIR/.venv/bin/pip" install -q --upgrade pip
    "$INSTALL_DIR/.venv/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt"
else
    echo "→ 虚拟环境已存在，跳过依赖安装"
fi

# ── 3. 构建 .app bundle ────────────────────────────────────────────────────────
echo "→ 构建 $APP_NAME.app ..."
rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Icon
if [ -f "$SYSTEM_ICON" ]; then
    cp "$SYSTEM_ICON" "$APP_BUNDLE/Contents/Resources/AppIcon.icns"
    ICON_KEY='<key>CFBundleIconFile</key>        <string>AppIcon</string>'
else
    ICON_KEY=""
fi

# Info.plist
cat > "$APP_BUNDLE/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>               <string>WhisperAIA</string>
  <key>CFBundleDisplayName</key>        <string>WhisperAIA</string>
  <key>CFBundleIdentifier</key>         <string>com.whisperaia.app</string>
  <key>CFBundleVersion</key>            <string>1.0.0</string>
  <key>CFBundleShortVersionString</key> <string>1.0.0</string>
  <key>CFBundlePackageType</key>        <string>APPL</string>
  <key>CFBundleExecutable</key>         <string>WhisperAIA</string>
  $ICON_KEY
  <key>NSHighResolutionCapable</key>    <true/>
  <key>LSMinimumSystemVersion</key>     <string>12.0</string>
  <key>NSMicrophoneUsageDescription</key>
  <string>WhisperAIA 需要麦克风权限以进行语音识别</string>
</dict>
</plist>
PLIST

# 启动脚本（安装时把路径写死进去）
cat > "$APP_BUNDLE/Contents/MacOS/$APP_NAME" << LAUNCHER
#!/bin/bash
exec "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/main.py"
LAUNCHER
chmod +x "$APP_BUNDLE/Contents/MacOS/$APP_NAME"

# ── 4. 完成 ────────────────────────────────────────────────────────────────────
echo ""
echo "✅ 安装完成！"
echo ""
echo "   应用位置: $APP_BUNDLE"
echo "   双击启动，或拖入 Dock / Applications 文件夹"
echo ""
echo "   卸载方法: rm -rf \"$APP_BUNDLE\" \"$INSTALL_DIR\""
