# WhisperAIA

本地免费语音输入工具，专为**中英文混合输入**设计（如"我们来聊一下 agent system 中 orchestration layer 的设计模式"）。

- 按住右 Option 说话，松开自动转写并粘贴到光标处
- 支持任意应用（VSCode、飞书、浏览器……）
- 全本地运行，无需联网，无费用
- 会根据你的纠错习惯持续变准

## 环境要求

- macOS（Apple Silicon 推荐，Intel 也可）
- Python 3.10+

## 安装

```bash
# 1. 安装系统依赖
brew install ollama portaudio

# 2. 启动 Ollama 服务
brew services start ollama

# 3. 拉取 LLM 模型（约 4.7GB，只需一次）
ollama pull qwen2.5:7b

# 4. 安装 Python 依赖
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## macOS 权限授权

系统设置 → 隐私与安全性 → 辅助功能 → 添加你的终端（Terminal / iTerm2）

## 运行

```bash
.venv/bin/python main.py
```

首次启动会下载 Whisper 模型（约 1.5GB），之后启动约 5 秒。

## 使用

| 操作 | 说明 |
|------|------|
| 按住右 Option | 开始录音 |
| 松开右 Option | 转写并自动粘贴 |
| 发现识别错误 | 改好后选中 → Cmd+C → 按右 Command |

纠错数据保存在 `~/.whisperaia/vocabulary.db`，累计越多识别越准。

## 性能参考（M3 Pro）

| 阶段 | 耗时 |
|------|------|
| Whisper 转写 | ~1s |
| LLM 后处理 | ~0.7s |
| 合计 | ~2s |
