# 安装和迁移

## 已有这台电脑的环境

本机已经配置好 `D:\GPT-SoVITS` 和 `.venv312`。解压完整模型包后可直接双击 `Start-WebUI.bat`，不必重新安装或训练。

## 新电脑

这是**专属模型和调用代码交付包**，不是包含所有基础环境的离线整合包。完整模型文件约 313 MiB；通用 GPT-SoVITS 运行环境需要另行准备。

1. 按 [GPT-SoVITS 官方说明](https://github.com/RVC-Boss/GPT-SoVITS#installation) 安装支持 **v2ProPlus** 的环境。当前验证使用的源码提交为 `04a44eb977586645f33594b72af13a035a2056c6`，官方仓库为 `RVC-Boss/GPT-SoVITS`。
2. 依据官方说明配置通用 BERT、HuBERT、G2PW、v2Pro/v2ProPlus 相关模型。推理所需目录至少包括：
   - `GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large`
   - `GPT_SoVITS/pretrained_models/chinese-hubert-base`
   - `GPT_SoVITS/pretrained_models/sv/pretrained_eres2netv2w24s4ep4.ckpt`
   - `GPT_SoVITS/text/G2PWModel`
3. 配置 FFmpeg。脚本优先寻找引擎下的 `runtime/ffmpeg.exe` 或 `ffmpeg.exe`，其次使用 PATH。
4. 下载本仓库 Release 中的完整 ZIP 并解压。复制 `runtime.example.json` 为 `runtime.local.json`，将 `engine_root` 改为引擎安装目录。
5. 使用引擎的 Python 安装本包前端依赖（已有本机环境可跳过）：

```powershell
& 'D:\GPT-SoVITS\.venv312\Scripts\python.exe' -m pip install -r .\requirements-client.txt
```

6. 双击 `Start-WebUI.bat`，或先用 CLI 合成一句短文本检查。

## 已验证的运行环境

- Windows，Python 3.12，CPU 推理。
- PyTorch / torchaudio 2.7.1+cpu。
- Gradio 4.44.1 / gradio_client 1.3.0，transformers 4.51.3。
- fastapi 0.115.6、starlette 0.41.3、pydantic 2.10.6。
- 具体前端依赖见 `requirements-client.txt`。`engine-requirements-tested.txt` 是原环境安装清单，供复现参考；其中含 Windows 专用 wheel，不是跨平台安装器。

默认启动器使用 CPU 和 float32，适配原电脑的 AMD 显卡环境。尚未验证其他系统、CUDA 环境或未来版本的 GPT-SoVITS，不应把它们描述为已测试。

## 工作方式

初次生成时，脚本验证包内权重和参考音频的 SHA-256，并把权重复制到引擎标准的权重目录。已有同名同内容文件会复用；同名但内容不同会报错，避免覆盖。

脚本从 GPT-SoVITS 调用原始推理结果，再执行包内原 A 柔顺处理。它不修改引擎源码，也不重新训练。推理服务只绑定 `127.0.0.1`，网页端口默认 9880，底层推理端口默认 9872。

## 完整性校验

发布页提供 ZIP 的 `.sha256` 文件。解压后还可运行：

```powershell
& 'D:\GPT-SoVITS\.venv312\Scripts\python.exe' -X utf8 .\verify_package.py
```

校验覆盖发布清单中的文件；`outputs`、`logs` 和本地配置不在发布校验范围内。
