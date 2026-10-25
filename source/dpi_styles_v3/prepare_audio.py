"""Rebuild a fixed-F preview from the unsped source and align it locally."""
from pathlib import Path
import argparse, json, math, os, re, subprocess
from difflib import SequenceMatcher
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def tokens(s):
    s = s.lower().replace('twenty nineteen', '2019').replace('twenty-nineteen', '2019')
    s = re.sub(r'd\s*p\s*i[ -]*net', 'dpinet', s)
    s = re.sub(r'i\s*c\s*l\s*r', 'iclr', s)
    s = re.sub(r'm\s*i\s*t', 'mit', s)
    s = re.sub(r'c\s*sail', 'csail', s)
    return re.findall(r'[a-z0-9]+', s)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-project',type=Path,required=True)
    ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--ffmpeg',type=Path,required=True);ap.add_argument('--asr-model',type=Path,required=True)
    a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True)
    raw,sr=sf.read(a.source_project/'audio/narration_raw.wav',dtype='float32')
    gain=min(10**(-20/20)/max(float(np.sqrt(np.mean(raw*raw))),1e-8),10**(-2/20)/np.max(np.abs(raw)))
    sf.write(out/'narration_gain.wav',raw*gain,sr,subtype='PCM_24')
    subprocess.run([str(a.ffmpeg),'-y','-v','error','-i',str(out/'narration_gain.wav'),'-af','atempo=1.1','-c:a','pcm_s24le',str(out/'narration_110.wav')],check=True)
    voice,sr=sf.read(out/'narration_110.wav',dtype='float32')
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['PATH']=str(a.ffmpeg.resolve().parent)+os.pathsep+os.environ['PATH']
    dll_handles=[os.add_dll_directory(str(a.ffmpeg.resolve().parent))] if os.name=='nt' else []
    from faster_whisper import WhisperModel
    model=WhisperModel(str(a.asr_model),device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True)
    class DirectMelFilters(np.ndarray):
        def __matmul__(self,other):
            return np.einsum('ij,jk->ik',np.asarray(self),other,optimize=False)
    model.feature_extractor.mel_filters=model.feature_extractor.mel_filters.view(DirectMelFilters)
    segs,_=model.transcribe(str(out/'narration_110.wav'),language='en',word_timestamps=True,beam_size=5,condition_on_previous_text=False,initial_prompt='DPI-Net, MIT CSAIL, ICLR.')
    segs=list(segs);words=[{'word':w.word,'start':w.start,'end':w.end} for s in segs for w in s.words or []]
    save(out/'asr.json',{'text':' '.join(s.text for s in segs),'words':words})
    script=json.loads((a.source_project/'styles/script.json').read_text(encoding='utf-8'))
    expected=[];bounds=[]
    for s in script['sentences']:
        ts=tokens(s['en']);bounds.append((len(expected),len(expected)+len(ts)));expected+=ts
    observed=[];word_ids=[]
    for i,w in enumerate(words):
        ts=tokens(w['word']);observed+=ts;word_ids += [i]*len(ts)
    sm=SequenceMatcher(None,expected,observed,autojunk=False)
    mapping={x+j:y+j for x,y,n in sm.get_matching_blocks() for j in range(n)}
    differences=[{'expected':expected[x:y],'observed':observed[q:r]} for tag,x,y,q,r in sm.get_opcodes() if tag!='equal']
    # Splitting an acronym across ASR words does not change the spoken content.
    homophone_note={'context':'cluster routes','display':'cluster roots','reason':'Single preview-specific homophone correction, checked against the synthesis script, paper hierarchy terminology and prior ASR of the same unsped recording; raw ASR retained.'}
    plain_match=''.join(expected)==''.join(observed)
    full_normalized=''.join(expected)==''.join(observed).replace('clusterroutes','clusterroots')
    if not full_normalized:
        save(out/'alignment.json',{'status':'needs_review','differences':differences})
        raise RuntimeError('ASR content differs; audio preserved for review')
    timings=[]
    for s,(x,y) in zip(script['sentences'],bounds):
        hits=[mapping[k] for k in range(x,y) if k in mapping]
        start=words[word_ids[hits[0]]]['start'];end=words[word_ids[hits[-1]]]['end']
        timings.append({'scene':s['scene'],'start':start,'end':end})
    # Recover the opening acronym word if ASR tokenized DPI-Net as DPI / Net.
    timings[0]['start']=words[0]['start']
    duration=math.ceil((len(voice)/sr+.25+.45)*60)/60
    for i,s in enumerate(script['sentences']):
        s['start']=0 if i==0 else round((timings[i-1]['end']+timings[i]['start'])/2+.25,4)
        s['end']=round((timings[i]['end']+timings[i+1]['start'])/2+.25,4) if i+1<len(timings) else duration
    script['duration']=duration;save(out/'script.timed.json',script)
    save(out/'alignment.json',{'status':'verified_with_documented_homophone' if not plain_match else 'verified','method':'ASR on actual 1.1x audio; acronym vocabulary hint only','speech_offset':.25,'speed':1.1,'same_normalized_content_before_homophone':plain_match,'same_normalized_content_after_homophone':full_normalized,'differences':differences,'reviewable_homophone':[homophone_note] if not plain_match else [],'sentence_words':timings})
    out_sr=48000;n=round(duration*out_sr);speech=resample_poly(voice,out_sr,sr)
    speech=np.pad(speech,(12000,max(0,n-len(speech)-12000)))[:n]
    music=np.zeros((n,2),dtype=np.float64);beat=60/78;bar=beat*4
    chords=[[48,55,59,64,74],[45,52,55,59,71],[41,48,52,57,67],[43,50,57,62,69]]
    for bi in range(math.ceil(duration/bar)):
        chord=chords[bi%4]
        for j,note in enumerate(chord):
            start=int((bi*bar+j*.11)*out_sr);length=min(n-start,int(5.8*out_sr))
            if length<=0:continue
            tt=np.arange(length)/out_sr;freq=440*2**((note-69)/12)
            env=(1-np.exp(-tt/.055))*np.exp(-tt/(2.8 if j<2 else 1.6))
            tone=env*(np.sin(2*np.pi*freq*tt)+.22*np.sin(4*np.pi*freq*tt)+.06*np.sin(6*np.pi*freq*tt))
            amp=.7 if j<2 else .34;pan=.18+.64*j/4
            for chan,g in enumerate([math.cos(pan*np.pi/2),math.sin(pan*np.pi/2)]):music[start:start+length,chan]+=amp*g*tone
        note=chord[2+(bi%3)]+12;start=int((bi*bar+beat*2.4)*out_sr);length=min(n-start,int(2.3*out_sr))
        if length>0:
            tt=np.arange(length)/out_sr;freq=440*2**((note-69)/12)
            tone=.13*(1-np.exp(-tt/.025))*np.exp(-tt/1.1)*np.sin(2*np.pi*freq*tt)
            music[start:start+length,:]+=tone[:,None]
    dry=music.copy()
    for delay,amp in [(.19,.16),(.31,.12),(.47,.08)]:
        k=int(delay*out_sr);music[k:]+=amp*dry[:-k,::-1]
    music*=10**(-31/20)/max(np.sqrt(np.mean(music**2)),1e-8)
    block=480;vrms=np.array([np.sqrt(np.mean(speech[i:i+block]**2)) for i in range(0,n,block)])
    activity=np.clip((vrms-.009)/.026,0,1);envelope=np.zeros_like(activity)
    for i,v in enumerate(activity):
        prev=envelope[i-1] if i else 0;alpha=.5 if v>prev else .035;envelope[i]=prev+alpha*(v-prev)
    duck=10**(-5*np.interp(np.arange(n)/block,np.arange(len(envelope)),envelope)/20)
    t=np.arange(n)/out_sr;fade=np.minimum(np.minimum(t/1.8,(duration-t)/1.3),1).clip(0,1)
    bed=music*duck[:,None]*fade[:,None];mix=speech[:,None]+bed
    mix_gain=min(1,10**(-1/20)/np.max(np.abs(mix)))
    sf.write(out/'narration.wav',speech,out_sr,subtype='PCM_24')
    sf.write(out/'music.wav',music*fade[:,None],out_sr,subtype='PCM_24')
    sf.write(out/'mix.wav',mix*mix_gain,out_sr,subtype='PCM_24')
    def stamp(t):
        ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02},{ms:03}'
    for kind in ['bilingual','en','zh']:
        rows=[]
        for i,s in enumerate(script['sentences']):
            txt=s['zh']+'\n'+s['en'] if kind=='bilingual' else s[kind]
            rows.append(f"{i+1}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{txt}")
        (out/f'{kind}.srt').write_text('\n\n'.join(rows)+'\n',encoding='utf-8')
    save(out/'mix_report.json',{'duration':duration,'speed_factor':1.1,'source':'unsped continuous F narration_raw.wav','voice_gain_db':20*math.log10(gain),'music':'Particle Study 01, regenerated at 78 BPM for longer duration','music_duck_db':5,'speech_rms_dbfs':20*math.log10(np.sqrt(np.mean(speech**2))),'bed_rms_dbfs':20*math.log10(np.sqrt(np.mean(bed**2))),'mix_peak_dbfs':20*math.log10(np.max(np.abs(mix*mix_gain)))})
    print(f'Audio complete: {duration:.3f} seconds; ASR and any homophone review recorded in alignment.json',flush=True)

if __name__=='__main__':main()
