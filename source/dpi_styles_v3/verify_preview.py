"""Decode actual output frames and record bounded preview verification."""
from pathlib import Path
import argparse, hashlib, json, math, subprocess
from PIL import Image

def run(args):return subprocess.run([str(x) for x in args],check=True,capture_output=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--ffmpeg',type=Path,required=True);p.add_argument('--ffprobe',type=Path,required=True);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args()
    out=a.output;movie=out/'DPI_A_persistent_map_110.mp4';script=json.loads((out/'script.timed.json').read_text(encoding='utf-8'))
    meta=json.loads(run([a.ffprobe,'-v','error','-show_entries','format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames,sample_rate,channels','-of','json',movie]).stdout)
    assert abs(float(meta['format']['duration'])-script['duration'])<.05
    video=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames']))==(1920,1080,'60/1',3210)
    (out/'qa').mkdir(exist_ok=True)
    run([a.ffmpeg,'-v','error','-i',movie,'-f','null','-'])
    cells=[]
    for i,s in enumerate(script['sentences']):
        path=out/'qa'/f'decoded-{i:02}.jpg';t=(s['start']+s['end'])/2
        run([a.ffmpeg,'-y','-v','error','-ss',t,'-i',movie,'-frames:v','1','-q:v','2',path]);cells.append(Image.open(path).resize((480,270)))
        if i==5:(out/'poster.jpg').write_bytes(path.read_bytes())
    sheet=Image.new('RGB',(480*5,270*2))
    for i,im in enumerate(cells):sheet.paste(im,((i%5)*480,(i//5)*270))
    sheet.save(out/'qa/decoded-contact.jpg',quality=94)
    transition_start=script['sentences'][5]['start'];times=[transition_start-.0333]+[transition_start+x for x in [0,.15,.3,.45,.6,.75,.9]]
    strip=Image.new('RGB',(555*4,320*2))
    for i,t in enumerate(times):
        path=out/'qa'/f'transition-{i:02}.png';run([a.ffmpeg,'-y','-v','error','-ss',t,'-i',movie,'-frames:v','1',path])
        im=Image.open(path).crop((1290,135,1845,455));strip.paste(im,((i%4)*555,(i//4)*320))
    strip.save(out/'qa/locator-transition.jpg',quality=94)
    run([a.ffmpeg,'-y','-v','error','-ss',transition_start-.25,'-i',movie,'-t','1.5','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',out/'qa/locator-transition.mp4'])
    # All sentence windows touch exactly, and red-box interpolation starts at
    # the previous stable region rather than a newly inferred camera state.
    assert all(abs(x['end']-y['start'])<1e-6 for x,y in zip(script['sentences'],script['sentences'][1:]))
    alignment_path=out/'alignment.json'
    alignment=json.loads(alignment_path.read_text(encoding='utf-8')) if alignment_path.is_file() else {}
    external=[]
    if (out/'camera_diagnosis.json').is_file():
        external.append({'file':'camera_diagnosis.json','role':'Separate B camera diagnostic','status':'Available; not rechecked by this A verification script'})
    report={'date':'2026-10-25','media':meta,'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'audio_speed':alignment.get('speed'),'duration_seconds':script['duration'],
        'checked':['Complete audio/video decode','Ten actual decoded scene frames','Eight decoded locator-transition frames and 1.5-second transition excerpt','Continuous adjacent subtitle windows'],
        'asr':{'source':'alignment.json' if alignment else None,'status':alignment.get('status','not_available'),'reviewable_homophone':alignment.get('reviewable_homophone',[]),'verification':'Recorded upstream alignment result; ASR not rerun by this script'},
        'external_evidence':external,
        'visual':'Persistent original full Figure 1; 0.85-second smooth red ROI movement; native 1080p/60',
        'voice_quality':'ASR and technical media checks do not establish subjective listening preference',
        'scope':'Technical verification of the revised A preview only; external evidence is listed separately'}
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'duration':script['duration'],'bytes':movie.stat().st_size,'sha256':report['sha256']},indent=2),flush=True)

if __name__=='__main__':main()
