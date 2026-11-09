# my-voice-a-smooth

当前保留的 **A 柔顺版 · 顺句优化** 专属声音模型。保留原始音高和原参考音色，提供本地网页、命令行和 agent 调用入口；AI 按用户指定的 **A＋挨（一声）** 朗读。

**完整模型请下载 [Release 中的 `my-voice-a-smooth-v1.0.0.zip`](https://github.com/qiu233333/my-voice-a-smooth/releases/tag/v1.0.0)。GitHub 自动生成的 Source code.zip 和普通 git clone 不含权重、参考音频或试听音频。**

## 直接使用

这台电脑已安装 `D:\GPT-SoVITS`。解压完整模型 ZIP，双击 **`Start-WebUI.bat`**，在打开的网页输入文字，再点击“生成语音”。新网页输出完整的 A 柔顺结果，默认地址为 `http://127.0.0.1:9880`。

音频保存在项目里的 `outputs` 文件夹，同时可以直接在网页试听和下载。

需要已有的 GPT-SoVITS v2ProPlus 推理环境。本包不包含 Python、FFmpeg 或数 GB 的通用预训练依赖；新电脑请先看 [安装说明](docs/INSTALL.md)。

## 命令行与 agent

```powershell
& 'D:\GPT-SoVITS\.venv312\Scripts\python.exe' -X utf8 `
  'D:\my-voice-a-smooth\synthesize.py' `
  --text '你好，欢迎使用我的声音。AI 的读音已经固定。' `
  --out 'D:\配音\示例.wav'
```

项目可以放在其他路径，只需替换上面的 `synthesize.py` 路径。模型文件全部使用相对路径。

- [自己使用：网页、导出、语速和常见问题](docs/USER_GUIDE.md)
- [agent 调用：稳定命令、返回值、排队和错误处理](AGENT_USAGE.md)
- [模型说明与来源](MODEL_CARD.md)
- [安装与迁移](docs/INSTALL.md)
- [第三方说明](THIRD_PARTY_NOTICES.md)

## 这一版包含什么

| 文件 | 用途 |
| --- | --- |
| `model/weights/my_voice_v1-e4.ckpt` | 专属 GPT 权重，4 轮训练后的推理版本 |
| `model/weights/my_voice_neutral_v1_e2_s216.pth` | 专属 SoVITS v2ProPlus 权重，2 轮训练 |
| `model/reference.wav` | 固定的 8.6 秒参考录音 |
| `model/voice.json` | 模型信息、参考文字、文件 SHA-256 |
| `model/A_smooth_v1.json` | 原 A 柔顺处理参数 |
| `model/A_fluent_v1.json` | 按句意分段、0.24 秒句间停顿 |
| `model/pronunciation_rules.json` | AI → 诶挨的固定发音规则 |
| `samples/A-smooth-preview.mp3` | 当前 A 版示例试听 |

本发布只提取当前可用版本，不包含原始录音全集、训练集、优化器、历史试作音色或旧检查点。原始项目仍保留在本机。

GitHub 常规 Git 文件限制为 100 MiB，因此两份较大的权重随 Release ZIP 分发，而不写入 Git 历史。参见 [GitHub 大文件说明](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)。
