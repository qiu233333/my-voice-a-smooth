"""Start an existing GPT-SoVITS engine without changing its source files."""
import argparse
import os
from pathlib import Path
import runpy
import sys
from voice_core import ROOT, prepare_model

parser=argparse.ArgumentParser()
parser.add_argument('--engine-root',required=True,type=Path)
parser.add_argument('--port',type=int,default=9872)
args=parser.parse_args()
engine=args.engine_root.resolve()
model=prepare_model(engine)
for folder in ['TEMP','logs']:
    (engine/folder).mkdir(exist_ok=True)
os.chdir(engine)
sys.path[:0]=[str(engine),str(engine/'GPT_SoVITS')]
os.environ.update({'language':'zh_CN','is_half':'False','is_share':'False','version':'v2ProPlus',
    'gpt_path':model['gpt']['engine_path'],'sovits_path':model['sovits']['engine_path'],
    'MYVOICE_REFERENCE':str(ROOT/model['reference_audio']),'MYVOICE_REFERENCE_TEXT':model['reference_text'],
    'infer_ttswebui':str(args.port),'OMP_NUM_THREADS':'8','MKL_NUM_THREADS':'8',
    'TEMP':str(engine/'TEMP'),'TMP':str(engine/'TEMP'),'NO_PROXY':'localhost,127.0.0.1,::1',
    'HF_HOME':str(engine/'cache/huggingface'),'MODELSCOPE_CACHE':str(engine/'cache/modelscope'),
    'CUDA_VISIBLE_DEVICES':''})
os.environ['PATH']=str(engine/'runtime')+os.pathsep+str(engine)+os.pathsep+os.environ.get('PATH','')
import torch
torch.set_num_threads(8)
import gradio as gr
original_launch=gr.Blocks.launch
def local_launch(self,*positional,**keywords):
    keywords.update(server_name='127.0.0.1',inbrowser=False,share=False)
    return original_launch(self,*positional,**keywords)
gr.Blocks.launch=local_launch
sys.argv=[str(engine/'GPT_SoVITS/inference_webui.py')]
runpy.run_path(sys.argv[0],run_name='__main__')
