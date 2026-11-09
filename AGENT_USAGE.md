# Agent 调用说明

目标：使用当前发布的 **A 柔顺版 · 顺句优化** 生成新文字。固定原音高、原参考音色和 AI 的“A＋挨（一声）”读音。不切换到其他音色，不重新训练。

## 前提

- 能访问解压后的本项目和本机 GPT-SoVITS 安装目录。
- 已下载完整模型 ZIP；`model/voice.json` 所列三个模型/参考文件均存在并通过 SHA-256 校验。
- 使用 GPT-SoVITS 自带的 Python，避免用系统 Python 混用依赖。

## 推荐调用

从任意工作目录执行，全部传绝对路径。长文先保存 UTF-8 文件，避免 shell 引号和特殊符号问题。

```powershell
& 'D:\GPT-SoVITS\.venv312\Scripts\python.exe' -X utf8 `
  'D:\my-voice-a-smooth\synthesize.py' `
  --text-file 'D:\文案\旁白.txt' `
  --out 'D:\配音\旁白.wav' `
  --engine-root 'D:\GPT-SoVITS'
```

短文本可用 `--text '这里是需要朗读的文字。'`。`--text` 和 `--text-file` 二选一。

| 参数 | 约定 |
| --- | --- |
| `--out` | 必填，WAV 或 MP3；父目录自动创建 |
| `--engine-root` | GPT-SoVITS 安装根目录；默认读配置或 `D:\GPT-SoVITS` |
| `--backend-port` | 默认 9872，始终连接本机回环地址 |
| `--speed` | 默认 1.0，范围 0.6–1.65 |
| `--preset smooth` | 可省略；此交付包只提供 A 柔顺版 |
| `--overwrite` | 仅当用户允许覆盖现有输出时添加 |

未运行的推理服务会自动在后台启动。Windows 进程不弹终端窗口。相同 GPT-SoVITS 安装上的本脚本会通过文件锁串行生成；在原电脑上也会复用旧项目的生成锁。

## 成功与失败

成功退出码为 0，**标准输出最后一行**为 JSON，例如：

```json
{"output":"D:\\配音\\旁白.wav","preset":"smooth","model_version":"1.0.0","duration_seconds":4.2,"sample_rate":32000,"pitch_shift_semitones":0}
```

完整报告同时写到 `<输出文件>.json`，包括原始 `text`、实际 `spoken_text`、速度和参数。检查退出码、文件存在且非空后再向用户报告成功。失败退出码非 0，标准错误输出包含原因；不要把失败或仅存在的旧文件当成新生成结果。

可以在自己的 Python 程序里调用：

```python
import json, subprocess
result = subprocess.run([
    r"D:\GPT-SoVITS\.venv312\Scripts\python.exe", "-X", "utf8",
    r"D:\my-voice-a-smooth\synthesize.py",
    "--text-file", r"D:\文案\旁白.txt",
    "--out", r"D:\配音\旁白.mp3",
], capture_output=True, text=True, encoding="utf-8", check=True)
report = json.loads(result.stdout.strip().splitlines()[-1])
print(report["output"])
```

## 行为约定

- 不改写用户提供的文案；确需润色时先在调用前形成明确的新文案。脚本只处理分句和指定的 AI 读音。
- 原模型权重、参考录音和柔顺算法保持固定，不叠加变调或其他音色处理。
- 不把日志、录音全集、缓存、环境凭证或其他任务文件上传到仓库。
- 音频生成成功不代表已人工试听；不要声称已验证主观听感。
- 云端 agent 和另一台电脑的 `127.0.0.1` 不是这台机器。此包没有配置公网服务；应在有本地文件和运行环境的机器上执行。

## 网页 API（可选）

启动 `Start-WebUI.bat` 后，9880 网页也提供 Gradio `/synthesize_a` 接口，参数为 `text`、`speed`、`format`。生产调用优先使用上述 CLI，它提供稳定的退出码和输出路径。
