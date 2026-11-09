# 自己使用 A 柔顺声音

## 本机最快用法

1. 下载完整模型 ZIP，并解压到一个长期保留的文件夹，例如 `D:\my-voice-a-smooth`。不要在 ZIP 预览窗口内直接运行。
2. 保持现有 `D:\GPT-SoVITS` 安装可用。
3. 双击项目里的 `Start-WebUI.bat`。
4. 浏览器打开 `http://127.0.0.1:9880` 后，输入需要朗读的文字。
5. 语速先用 `1.0`，选择 WAV 或 MP3，点“生成语音”。
6. 在网页试听、下载。项目内 `outputs` 文件夹也会保留音频和对应的 JSON 参数记录。

首次调用会自动启动底层推理服务，CPU 生成需要等待。后续会复用服务；重复点击前先等本次任务完成。

## 两个网页的区别

- **9880：本交付包的简化网页。** 固定使用 A 柔顺版，包含顺句、AI 读音与柔顺处理，适合日常使用。
- **9872：GPT-SoVITS 原始推理网页。** 可以手工换模型和参考录音；它直接输出模型原声，不等于本交付包的完整柔顺结果。

## 文案怎么写更顺

按正常语义写完整句子，使用逗号、句号、问号和换行。脚本会按句末标点分段；过长句子在已有中文逗号处分段，不会自动改写词语。

例子见 `samples/example.txt`。示例将“角色卡”写成“角色卡片”，将“做客的朋友，这样……”拆成两句。这些是示例文案的调整，不是自动替换所有文本的规则。

独立出现的 `AI`、`ai`、`A I` 使用“诶挨”，第二音为 `ai1`。`OpenAI` 和英文标识符中的 AI 不替换。其他人名、多音字或英文缩写仍需要试听检查。

## 语速和保存

语速可选 0.6–1.65，默认 1.0。轻微调整建议 0.9–1.1。

WAV 为 32 kHz PCM 音频，适合后期剪辑；MP3 为 192 kbps，适合分享。网页每次使用不同文件名，避免覆盖已有结果。

## GPT-SoVITS 不在 D 盘原路径

复制 `runtime.example.json` 为 `runtime.local.json`，把 `engine_root` 改成实际安装目录，例如：

```json
{"engine_root":"E:/GPT-SoVITS","backend_port":9872}
```

也可以运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-WebUI.ps1 -EngineRoot 'E:\GPT-SoVITS'
```

## 常见问题

- **提示找不到权重：** 确认下载的是 Release 的完整模型 ZIP，不是 Source code.zip。
- **提示找不到 Python：** 检查 `engine_root`。支持 `.venv312\Scripts\python.exe`、`.venv\Scripts\python.exe` 和整合包的 `runtime\python.exe`。
- **启动失败：** 查看项目 `logs/web-error.log` 和 `logs/engine-error.log`，按照安装说明检查依赖。
- **生成已有文件时报错：** CLI 默认不覆盖；换一个文件名，或明确增加 `--overwrite`。
- **音色意外改变：** 使用本包 9880 网页或 `synthesize.py`，保留模型、参考音频和配置。不要在 9872 网页同时手工切换模型。

网页和推理服务只监听本机 `127.0.0.1`。结束使用时可以关闭网页；后台服务会继续存在以便再次生成。需要释放资源时，结束对应 `engine_runner.py` 或 `webui.py` 的 Python 进程即可，不要结束其他任务的 Python。
