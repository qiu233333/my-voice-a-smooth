"""Small web page that returns the complete A smooth result."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import uuid
import gradio as gr
from voice_core import ROOT, synthesize

parser=argparse.ArgumentParser()
parser.add_argument('--engine-root',type=Path)
parser.add_argument('--backend-port',type=int)
parser.add_argument('--port',type=int,default=9880)
args=parser.parse_args()

def generate(text,speed,format):
    if not text.strip():
        raise gr.Error('请先输入要朗读的文字。')
    output=ROOT/'outputs'/f'{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}.{format}'
    try:
        report=synthesize(text,output,args.engine_root,args.backend_port,float(speed))
    except Exception as error:
        raise gr.Error(str(error)) from error
    return str(output),str(output),f'已生成，时长 {report["duration_seconds"]:.2f} 秒。文件已保存到 outputs 文件夹。'

with gr.Blocks(title='A 柔顺声音',analytics_enabled=False) as app:
    gr.Markdown('# A 柔顺声音\n输入文字即可生成。保留原音色，自动整理分句和停顿；AI 按“A＋挨（一声）”朗读。')
    text=gr.Textbox(label='朗读文字',lines=7,placeholder='在这里输入需要朗读的内容……')
    with gr.Row():
        speed=gr.Slider(.6,1.65,value=1.0,step=.05,label='语速')
        format=gr.Radio(['wav','mp3'],value='wav',label='文件格式')
    button=gr.Button('生成语音',variant='primary')
    audio=gr.Audio(label='试听',type='filepath')
    download=gr.File(label='下载音频')
    status=gr.Textbox(label='状态',interactive=False)
    button.click(generate,[text,speed,format],[audio,download,status],api_name='synthesize_a',concurrency_limit=1)
app.queue().launch(server_name='127.0.0.1',server_port=args.port,share=False,inbrowser=False)
