"""Inspect the old B camera and render a short continuous-sampling correction."""
from pathlib import Path
import argparse, importlib.util, json, math, os, subprocess
from PIL import Image, ImageDraw

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-styles',type=Path,required=True);p.add_argument('--ffmpeg',type=Path,required=True);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent)
    a=p.parse_args();out=a.output/'qa';out.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location('old_styles',a.source_styles/'render.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    clips=[]
    for i,t in enumerate([12.28,12.32,13,13.25,13.5,13.75,14]):
        dest=out/f'B-original-{i:02}.png'
        subprocess.run([str(a.ffmpeg),'-y','-v','error','-ss',str(t),'-i',str(a.source_styles/'deliverables/DPI_microscope.mp4'),'-frames:v','1',str(dest)],check=True)
        clips.append(Image.open(dest).resize((640,360)))
    sheet=Image.new('RGB',(640*4,360*2),'#222222')
    for i,im in enumerate(clips):sheet.paste(im,((i%4)*640,(i//4)*360))
    sheet.save(out/'B-original-contact.jpg',quality=94)
    # Stable sampling directly from the full-resolution source. ROI itself is
    # interpolated by the original renderer from fixed endpoints and time.
    def continuous_panel(im,roi,box,scale=1):
        mapper=old.crop_camera(im,roi,box,1.0)
        x,y,w,h=box;l,t,r,b=roi;left,top=mapper((l,t));right,bottom=mapper((r,b));d=ImageDraw.Draw(im)
        # Letterbox outside the selected source region, while the image itself
        # remains sampled with one floating-point transform.
        for rect in [(x,y,left,y+h),(right,y,x+w,y+h),(left,y,right,top),(left,bottom,right,y+h)]:
            if rect[2]>rect[0] and rect[3]>rect[1]:d.rectangle(rect,fill='white')
        return mapper
    old.focused_figure=continuous_panel
    start,end,fps=12.0,14.5,60
    cmd=[str(a.ffmpeg),'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output/'B_camera_fixed_12_14_5.mp4')]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,creationflags=0x08000000 if os.name=='nt' else 0)
    for n in range(round((end-start)*fps)):proc.stdin.write(old.render_frame(start+n/fps,'microscope').tobytes())
    proc.stdin.close();assert proc.wait()==0
    for i,t in enumerate([12.28,12.32,13,13.25,13.5,13.75,14]):old.render_frame(t,'microscope').save(out/f'B-fixed-{i:02}.jpg',quality=94)
    # Track a source landmark in the settled 13.2-14.0 interval. The old crop
    # then resize quantizes its translation; the corrected transform is float.
    rows=[];s=old.SCRIPT['sentences'][2]
    for n in range(25):
        t=13+n/24;p=(t-s['start'])/(s['end']-s['start']);u=old.ease(p/.25)
        roi=[old.lerp(x,y,u) for x,y in zip(old.ROIS[1],old.ROIS[2])]
        l,top,r,b=roi;z=min(1160/(r-l),390/(b-top))*old.lerp(.92,1.02,old.ease(p))
        nw=round((round(r)-round(l))*z);nh=round((round(b)-round(top))*z)
        px=round(60+(1160-nw)/2);py=round(145+(390-nh)/2)
        intended_x=60+580+(400-(l+r)/2)*z;intended_y=145+195+(220-(top+b)/2)*z
        actual_x=px+(400-round(l))*nw/(round(r)-round(l));actual_y=py+(220-round(top))*nh/(round(b)-round(top))
        rows.append({'time':round(t,5),'quantized_x':actual_x,'quantized_y':actual_y,'ideal_x':intended_x,'ideal_y':intended_y,'error_px':math.hypot(actual_x-intended_x,actual_y-intended_y)})
    report={'inspected_original_video':'DPI_microscope.mp4','original_fps':24,'range_seconds':[12.28,14],
        'confirmed_code_findings':['Float ROI is rounded by crop, rounded again by resize dimensions and paste coordinates.','At a new sentence, scale restarts at 0.92 after the previous sentence approaches 1.02.','At 12.32 the dynamic-graph transition begins from the input panel; transition ends about 13.185.'],
        'relative_scale_reset':.92/1.02,'sample_max_landmark_quantization_error_px':max(x['error_px'] for x in rows),'landmark_samples':rows,
        'correction':'Direct affine sampling of the full source with float camera coordinates; constant magnification factor at sentence boundaries; preview encoded at 60 fps.',
        'scope':'2.5-second corrected B diagnostic, not a newly rendered full B film. Quantization and scale reset are confirmed defects; they do not establish the sole cause of every reported subjective shake.'}
    (a.output/'camera_diagnosis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('B camera diagnostic complete',flush=True)

if __name__=='__main__':main()
