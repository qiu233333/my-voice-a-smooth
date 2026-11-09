"""Portable A-smooth client. Model files are relative to this project."""
from pathlib import Path
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def settings(engine_root=None, port=None):
    local_path = ROOT / 'runtime.local.json'
    local = read_json(local_path) if local_path.exists() else {}
    engine = Path(engine_root or os.environ.get('GPT_SOVITS_ROOT') or local.get('engine_root', 'D:/GPT-SoVITS')).expanduser().resolve()
    selected_port = int(port or os.environ.get('MYVOICE_BACKEND_PORT') or local.get('backend_port', 9872))
    if not 1024 <= selected_port <= 65535:
        raise ValueError('Backend port must be 1024-65535.')
    return engine, selected_port


def find_python(engine):
    for relative in ['.venv312/Scripts/python.exe', '.venv/Scripts/python.exe', 'runtime/python.exe', '.venv/bin/python']:
        candidate = engine / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError('No GPT-SoVITS Python runtime found. Read docs/INSTALL.md or set --engine-root.')


def find_ffmpeg(engine):
    for relative in ['runtime/ffmpeg.exe', 'ffmpeg.exe', 'runtime/ffmpeg']:
        candidate = engine / relative
        if candidate.is_file():
            return candidate
    command = shutil.which('ffmpeg')
    if command:
        return Path(command)
    raise FileNotFoundError('FFmpeg not found in GPT-SoVITS or PATH.')


def model_manifest():
    return read_json(ROOT / 'model/voice.json')


def prepare_model(engine):
    if not (engine / 'GPT_SoVITS/inference_webui.py').is_file():
        raise FileNotFoundError(f'Not a GPT-SoVITS installation: {engine}')
    model = model_manifest()
    # Validate all packaged artifacts before copying or invoking inference.
    for entry in model['artifacts']:
        source = ROOT / entry['path']
        if not source.is_file():
            raise FileNotFoundError(f'{source} is missing. Download the full model ZIP from GitHub Releases, not Source code.zip.')
        if sha256(source) != entry['sha256']:
            raise ValueError(f'Model integrity check failed: {entry["path"]}')
    for key in ['gpt', 'sovits']:
        spec = model[key]
        source = ROOT / spec['package_path']
        destination = engine / spec['engine_path']
        if destination.exists():
            if sha256(destination) != sha256(source):
                raise FileExistsError(f'A different checkpoint already exists at {destination}; it was not overwritten.')
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + '.' + uuid.uuid4().hex + '.tmp')
            try:
                shutil.copy2(source, temporary)
                os.replace(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)
    return model


@contextlib.contextmanager
def queue_lock(engine):
    # Reuse the original project's lock when installed on the original computer.
    legacy = engine / 'voices/my_voice/agent_generation.lock'
    path = legacy if legacy.parent.is_dir() else engine / 'TEMP/my-voice-a-smooth.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        deadline = time.monotonic() + 1800
        while True:
            stream.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (OSError, BlockingIOError):
                if time.monotonic() > deadline:
                    raise TimeoutError('Timed out waiting for another synthesis job.')
                time.sleep(.3)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def ensure_server(engine, port, python):
    import requests
    url = f'http://127.0.0.1:{port}'
    session = requests.Session()
    session.trust_env = False
    def ready():
        try:
            response = session.get(url + '/config', timeout=3)
            return response.status_code == 200 and any(d.get('api_name') == 'get_tts_wav' for d in response.json().get('dependencies', []))
        except (requests.RequestException, ValueError):
            return False
    if ready():
        return url
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    with (logs / 'engine.log').open('a', encoding='utf-8') as stdout, (logs / 'engine-error.log').open('a', encoding='utf-8') as stderr:
        process = subprocess.Popen([str(python), '-X', 'utf8', '-u', str(ROOT / 'engine_runner.py'), '--engine-root', str(engine), '--port', str(port)],
                                   cwd=engine, stdout=stdout, stderr=stderr,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        if ready():
            return url
        if process.poll() is not None:
            raise RuntimeError(f'Engine exited. See {logs / "engine-error.log"}')
        time.sleep(1)
    raise TimeoutError(f'Engine startup timed out. See {logs / "engine-error.log"}')


def synthesize(text, output, engine_root=None, port=None, speed=1.0, overwrite=False):
    import numpy as np
    import soundfile as sf
    from gradio_client import Client, handle_file
    from pronunciation import spoken_form
    from prosody import prepare_fluent_text
    if not text.strip():
        raise ValueError('Text is empty.')
    if not .6 <= speed <= 1.65:
        raise ValueError('Speed must be between 0.6 and 1.65.')
    output = Path(output).expanduser().resolve()
    if output.suffix.lower() not in ['.wav', '.mp3']:
        raise ValueError('Output must end in .wav or .mp3.')
    report_path = output.with_suffix(output.suffix + '.json')
    if not overwrite and (output.exists() or report_path.exists()):
        raise FileExistsError(f'Output already exists: {output}')
    engine, port = settings(engine_root, port)
    python, ffmpeg = find_python(engine), find_ffmpeg(engine)
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'
    os.environ['no_proxy'] = os.environ['NO_PROXY']
    temporary_root = ROOT / '.work'
    temporary_root.mkdir(exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = str(temporary_root)
    started = time.monotonic()
    spoken = prepare_fluent_text(spoken_form(text))
    profile = read_json(ROOT / 'model/A_fluent_v1.json')
    parameters = {key: profile[key] for key in ['how_to_cut', 'pause_second', 'temperature', 'top_k', 'top_p']}
    with queue_lock(engine):
        if not overwrite and (output.exists() or report_path.exists()):
            raise FileExistsError(f'Output already exists: {output}')
        model = prepare_model(engine)
        url = ensure_server(engine, port, python)
        with tempfile.TemporaryDirectory(prefix='job_', dir=temporary_root) as directory:
            work = Path(directory)
            client = Client(url, verbose=False)
            client.predict(api_name='/change_choices')
            client.predict(gpt_path=model['gpt']['engine_path'], api_name='/change_gpt_weights')
            client.predict(sovits_path=model['sovits']['engine_path'], prompt_language='中文', text_language='中英混合', api_name='/change_sovits_weights')
            raw = client.predict(ref_wav_path=handle_file(str(ROOT / model['reference_audio'])), prompt_text=model['reference_text'],
                                 prompt_language='中文', text=spoken, text_language='中英混合', speed=speed,
                                 inp_refs=None, if_freeze=False, **parameters, api_name='/get_tts_wav')
            completed = subprocess.run([str(python), '-X', 'utf8', str(ROOT / 'smooth_A.py'), '--input', str(raw),
                                        '--output-dir', str(work / 'smooth'), '--ffmpeg', str(ffmpeg)], capture_output=True, text=True, encoding='utf-8')
            if completed.returncode:
                raise RuntimeError(completed.stderr or completed.stdout)
            source = work / 'smooth/专属模型V1_A柔顺修整.wav'
            data, sample_rate = sf.read(source)
            if not len(data) or not np.isfinite(data).all() or sample_rate != 32000:
                raise RuntimeError('Invalid generated audio.')
            staged = work / ('result' + output.suffix.lower())
            codec = ['-c:a', 'libmp3lame', '-b:a', '192k'] if output.suffix.lower() == '.mp3' else ['-c:a', 'pcm_s16le']
            subprocess.run([str(ffmpeg), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source), '-ar', '32000', *codec, str(staged)], check=True)
            output.parent.mkdir(parents=True, exist_ok=True)
            sibling = output.with_name(output.name + '.' + uuid.uuid4().hex + '.tmp')
            try:
                shutil.copy2(staged, sibling)
                os.replace(sibling, output)
            finally:
                sibling.unlink(missing_ok=True)
            report = {'output': str(output), 'preset': 'smooth', 'model_version': model['release_version'],
                      'text': text, 'spoken_text': spoken, 'speed': speed, 'pitch_shift_semitones': 0,
                      'duration_seconds': round(len(data) / sample_rate, 3), 'sample_rate': sample_rate,
                      'inference_settings': parameters, 'elapsed_seconds': round(time.monotonic() - started, 2),
                      'human_listening_assessment': False}
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            return report
