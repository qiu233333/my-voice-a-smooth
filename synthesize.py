"""Stable command-line entry point for people and agents."""
import argparse
import json
import sys
from pathlib import Path
from voice_core import synthesize

def main():
    parser=argparse.ArgumentParser(description='Generate speech with the extracted A smooth voice.')
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--text')
    source.add_argument('--text-file',type=Path,help='UTF-8 text; BOM supported')
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--engine-root',type=Path)
    parser.add_argument('--backend-port',type=int)
    parser.add_argument('--speed',type=float,default=1.0)
    parser.add_argument('--preset',choices=['smooth'],default='smooth')
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args()
    text=args.text if args.text is not None else args.text_file.read_text(encoding='utf-8-sig')
    report=synthesize(text,args.out,args.engine_root,args.backend_port,args.speed,args.overwrite)
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'error':str(error)},ensure_ascii=False),file=sys.stderr,flush=True)
        sys.exit(1)
