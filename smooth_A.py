from pathlib import Path
import argparse,json,subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfiltfilt
from scipy.ndimage import uniform_filter1d

root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--input',required=True)
parser.add_argument('--output-dir',required=True)
parser.add_argument('--ffmpeg',required=True)
args=parser.parse_args()
source=Path(args.input);out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
ffmpeg=Path(args.ffmpeg)
profile={'name':'A 柔顺修整 V1','source_style':'自然中性 A','pitch_shift_semitones':0,'time_stretch':1.0,'declick':'adeclick=w=25:o=75:a=2:t=5:b=1','highpass_hz':55,'dynamic_bands':[{'low_hz':180,'high_hz':650,'threshold_percentile':70,'max_extra_cut_db':2.2,'static_cut_db':0.4,'slope':1.5},{'low_hz':850,'high_hz':1800,'threshold_percentile':75,'max_extra_cut_db':1.2,'static_cut_db':0.0,'slope':0.7}],'gain_attack_ms':18,'gain_release_ms':130,'compressor':'acompressor=threshold=0.18:ratio=1.35:attack=12:release=100:makeup=1:knee=2.8:detection=rms','target_loudness_lufs':-18,'true_peak_limit_dbtp':-1.5,'limitations':'Light post-processing can reduce impulsive roughness and prominent resonances; it cannot completely reconstruct a constricted synthesized syllable or guarantee perceived smoothness.'}
prepared=out/'01_declick_float.wav'
first_filter=profile['declick']+f",highpass=f={profile['highpass_hz']},loudnorm=I=-18:TP=-1.5:LRA=11"
p=subprocess.run([str(ffmpeg),'-hide_banner','-y','-i',str(source),'-af',first_filter,'-ar','32000','-ac','1','-c:a','pcm_f32le',str(prepared)],capture_output=True,text=True,errors='replace',check=True)
(out/'declick.log').write_text(p.stderr,encoding='utf-8')
x,sr=sf.read(prepared,dtype='float64');original,original_sr=sf.read(source,dtype='float64')
assert sr==original_sr==32000 and len(x)==len(original)
frame=round(sr*.024);hop=round(sr*.010)
envelope=np.sqrt(np.maximum(uniform_filter1d(x*x,size=frame),1e-14))
positions=np.arange(0,len(x),hop)
voiced=envelope[positions]>max(.015,float(np.quantile(envelope,.65))*.25)
if np.count_nonzero(voiced)<3:
    raise ValueError('Audio has too little voiced signal for smoothing.')
y=x.copy();band_reports=[]
for spec in profile['dynamic_bands']:
    band=sosfiltfilt(butter(2,[spec['low_hz'],spec['high_hz']],btype='bandpass',fs=sr,output='sos'),y)
    band_env=np.sqrt(np.maximum(uniform_filter1d(band*band,size=frame),1e-14))
    ratio=20*np.log10((band_env[positions]+1e-9)/(envelope[positions]+1e-9))
    threshold=float(np.percentile(ratio[voiced],spec['threshold_percentile']))
    cut=np.clip((ratio-threshold)*spec['slope'],0,spec['max_extra_cut_db'])+spec['static_cut_db']
    cut*=np.clip(envelope[positions]/.025,0,1)
    smooth=np.empty_like(cut);previous=0.0
    for i,target in enumerate(cut):
        tau=profile['gain_attack_ms'] if target>previous else profile['gain_release_ms']
        coefficient=np.exp(-hop/(sr*tau/1000))
        previous=coefficient*previous+(1-coefficient)*target;smooth[i]=previous
    gain=np.interp(np.arange(len(x)),positions,10**(-smooth/20))
    y+=band*(gain-1)
    band_reports.append({'band_hz':[spec['low_hz'],spec['high_hz']],'adaptive_threshold_db':threshold,'max_control_cut_db':float(smooth.max()),'mean_control_cut_db_on_voice':float(smooth[voiced].mean())})
assert np.isfinite(y).all()
intermediate=out/'02_dynamic_resonance_float.wav';sf.write(intermediate,y,sr,subtype='FLOAT')
wav=out/'专属模型V1_A柔顺修整.wav';mp3=out/'专属模型V1_A柔顺修整.mp3'
tail_filter=profile['compressor']+',loudnorm=I=-18:TP=-1.5:LRA=11'
subprocess.run([str(ffmpeg),'-hide_banner','-loglevel','error','-y','-i',str(intermediate),'-af',tail_filter,'-ar',str(sr),'-c:a','pcm_s16le',str(wav)],check=True)
subprocess.run([str(ffmpeg),'-hide_banner','-loglevel','error','-y','-i',str(wav),'-c:a','libmp3lame','-b:a','192k',str(mp3)],check=True)
final,final_sr=sf.read(wav)
assert final_sr==sr and len(final)==len(original) and np.isfinite(final).all() and np.max(np.abs(final))<1
report={'source':str(source),'wav':str(wav),'mp3':str(mp3),'sample_rate':sr,'duration_seconds':len(final)/sr,'sample_count_unchanged':True,'peak':float(np.max(np.abs(final))),'profile':profile,'dynamic_band_processing':band_reports,'human_listening_assessment':False}
(out/'processing_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='profile'},ensure_ascii=False,indent=2),flush=True)
