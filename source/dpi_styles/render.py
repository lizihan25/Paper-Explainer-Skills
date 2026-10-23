"""Independent deterministic paper explainer; no inherited layout components.

Use --stills for visual QA, --style all for silent movies. Timings come from
script.timed.json when available, so one edit retimes all three treatments. Generated moving
particle diagrams are explanatory schematics, not neural simulation results.
"""
from pathlib import Path
import argparse, json, math, os, subprocess, shutil, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SCRIPT_PATH = ROOT / ('script.timed.json' if (ROOT/'script.timed.json').exists() else 'script.json')
SCRIPT = json.loads(SCRIPT_PATH.read_text(encoding='utf-8'))
W, H = 1280, 720
FPS = 24
PAPER = Image.open(ROOT/'assets/dpi_net_method.png').convert('RGB')
RESULT = Image.open(ROOT/'assets/dpi_net_fig4.png').convert('RGB')
PORTRAIT = Image.open(ROOT/'assets/yunzhu-li.jpg').convert('RGB') if (ROOT/'assets/yunzhu-li.jpg').exists() else None
DEFAULT_FONTDIR = Path(os.environ['WINDIR'])/'Fonts' if 'WINDIR' in os.environ else ROOT/'fonts'
FONTDIR = Path(os.environ.get('FONT_DIR', str(DEFAULT_FONTDIR)))
FONT_PATHS = {
    (False, False): Path(os.environ.get('FONT_REGULAR', str(FONTDIR/'msyh.ttc'))),
    (False, True): Path(os.environ.get('FONT_BOLD', str(FONTDIR/'msyhbd.ttc'))),
    (True, False): Path(os.environ.get('FONT_SERIF', str(FONTDIR/'cambria.ttc'))),
    (True, True): Path(os.environ.get('FONT_SERIF_BOLD', str(FONTDIR/'cambriab.ttf'))),
}
FONTS = {}
FULL_PALETTE = json.loads((ROOT/'palette_3b1b.json').read_text(encoding='utf-8'))['colors']
COLORS = {name:FULL_PALETTE[name+'_c'] for name in ['blue','teal','green','yellow','gold','red','maroon','purple','grey']}
TITLES = ['A simulator made of particles','State enters as particles','Who interacts with whom?','Local messages','Several hops. One time step.','Leaf → root → root → leaf','Predict the next state','Turn prediction into control','Execute → observe → replan','Follow motion. Pass effects. Connect distant parts.']
ROIS = [(0,0,1852,860),(900,530,1852,860),(20,15,900,490),(900,0,1852,525),(10,540,900,850),(900,0,1852,525),(900,530,1852,860),(900,530,1852,860),(900,530,1852,860),(0,0,1852,860)]

def f(size, serif=False, bold=False):
    key=(size,serif,bold)
    if key not in FONTS:
        path=FONT_PATHS[(serif,bold)]
        FONTS[key]=ImageFont.truetype(str(path),size)
    return FONTS[key]

def ease(x):
    x=max(0,min(1,x));return x*x*(3-2*x)

def lerp(a,b,p):return a+(b-a)*p

def text(im, xy, s, size=28, color='#ffffff', serif=False, bold=False, anchor=None):
    ImageDraw.Draw(im).text(xy,s,font=f(size,serif,bold),fill=color,anchor=anchor)

def wrap(s,font,width):
    words=s.split(' ') if ' ' in s and not any('\u4e00'<=c<='\u9fff' for c in s) else list(s)
    sep=' ' if words!=list(s) else ''
    out=[];line=''
    for word in words:
        candidate=line+sep+word if line else word
        if font.getlength(candidate)>width and line:out.append(line);line=word
        else:line=candidate
    if line:out.append(line)
    return out

def arrow(im,a,b,color,width=3,head=10):
    d=ImageDraw.Draw(im);d.line([a,b],fill=color,width=width)
    dx,dy=b[0]-a[0],b[1]-a[1];ang=math.atan2(dy,dx)
    d.polygon([b,(b[0]-head*math.cos(ang-.5),b[1]-head*math.sin(ang-.5)),(b[0]-head*math.cos(ang+.5),b[1]-head*math.sin(ang+.5))],fill=color)

def dot(im,p,r=7,color='#58C4DD'):
    ImageDraw.Draw(im).ellipse((p[0]-r,p[1]-r,p[0]+r,p[1]+r),fill=color)

def fit(im,src,box):
    x,y,w,h=box;scale=min(w/src.width,h/src.height)
    nw,nh=int(src.width*scale),int(src.height*scale)
    im.paste(src.resize((nw,nh),Image.Resampling.LANCZOS),(int(x+(w-nw)/2),int(y+(h-nh)/2)))

def crop_camera(im,roi,box,scale=1):
    # Every camera is derived from one full source image, preserving provenance.
    x,y,w,h=box; l,t,r,b=roi;cx=(l+r)/2;cy=(t+b)/2
    z=min(w/(r-l),h/(b-t))*scale
    coeff=(1/z,0,cx-w/(2*z),0,1/z,cy-h/(2*z))
    view=PAPER.transform((int(w),int(h)),Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC,fillcolor='white')
    im.paste(view,(int(x),int(y)))
    return lambda pt:(x+w/2+(pt[0]-cx)*z,y+h/2+(pt[1]-cy)*z)

def focused_figure(im,roi,box,scale=1):
    # Isolate the source panel, then magnify it; neighboring panels cannot intrude.
    x,y,w,h=box;l,t,r,b=roi;z=min(w/(r-l),h/(b-t))*scale
    src=PAPER.crop((l,t,r,b));nw,nh=round(src.width*z),round(src.height*z)
    px,py=round(x+(w-nw)/2),round(y+(h-nh)/2)
    im.paste(src.resize((nw,nh),Image.Resampling.LANCZOS),(px,py))
    return lambda pt:(px+(pt[0]-l)*z,py+(pt[1]-t)*z)

def frame_roi(im,box,color='#e08230',width=3):
    x,y,r,b=box;d=ImageDraw.Draw(im);s=19
    for px,py,sx,sy in [(x,y,1,1),(r,y,-1,1),(x,b,1,-1),(r,b,-1,-1)]:
        d.line([(px+sx*s,py),(px,py),(px,py+sy*s)],fill=color,width=width)

def subtitles(im,sent):
    d=ImageDraw.Draw(im);d.rectangle((0,600,W,H),fill='#101519')
    zh=wrap(sent['zh'],f(25),1160);en=wrap(sent['en'],f(19),1160)
    y=612
    for line in zh:
        text(im,(W/2,y),line,25,'#ffffff',anchor='mt');y+=32
    y=max(650,y+1)
    for line in en:
        text(im,(W/2,y),line,19,'#d4d8dc',anchor='mt');y+=26

def graph(im,box,t,mode='dynamic',dark=True):
    x,y,w,h=box;d=ImageDraw.Draw(im)
    palette=[COLORS[k] for k in ['blue','teal','green','gold','red','purple']]
    fg='#ffffff' if dark else '#182d36';edge='#405259' if dark else '#bdc8c7'
    points=[]
    for j in range(4):
        for i in range(7):
            px=x+60+i*(w-120)/6+math.sin(t*1.1+j*1.7+i*.6)*18
            py=y+30+j*(h-60)/3+math.cos(t*.8+i*1.4+j)*12
            points.append((px,py))
    links=[]
    for a in range(len(points)):
        for b in range(a+1,len(points)):
            dist=math.dist(points[a],points[b])
            if dist<min(w/5.5,h/2.3):
                links.append((a,b));d.line([points[a],points[b]],fill=edge,width=2)
    if mode in ['local','multistep','dynamic']:
        for k,(a,b) in enumerate(links):
            if k%3==int(t)%3:
                p=(t*.7+k*.173)%1
                q=(lerp(points[a][0],points[b][0],p),lerp(points[a][1],points[b][1],p))
                dot(im,q,4,COLORS['yellow'] if dark else '#b55d1b')
    for k,p in enumerate(points):
        dot(im,p,8,palette[k%len(palette)])
    if mode=='input':
        p=points[9];d.ellipse((p[0]-26,p[1]-26,p[0]+26,p[1]+26),outline=COLORS['yellow'] if dark else '#b55d1b',width=2)
        arrow(im,p,(p[0]+50,p[1]-34),COLORS['gold'],3)
    return points

def hierarchy(im,box,t,dark=True):
    x,y,w,h=box;d=ImageDraw.Draw(im);cols=[COLORS[k] for k in ['blue','teal','gold','red']]
    roots=[(x+w*(.15+i*.235),y+65+25*math.sin(i)) for i in range(4)]
    for a in range(4):
        for b in range(a+1,4):
            d.line([roots[a],roots[b]],fill='#344c54' if dark else '#b7c7c4',width=2)
    pts=[]
    for i,root in enumerate(roots):
        for j in range(5):
            p=(x+w*(.055+i*.235+j*.045),y+h*.82+math.sin(j*2+i)*25);pts.append(p)
            d.line([p,root],fill='#41565c' if dark else '#c4c4b6',width=2)
            phase=(t*.45-j*.09)%1
            if int(t*.45)%2:phase=1-phase
            q=(lerp(p[0],root[0],phase),lerp(p[1],root[1],phase))
            dot(im,q,4,cols[i]);dot(im,p,7,cols[i])
        if i<3:
            arrow(im,root,roots[i+1],cols[i],3)
            phase=(t*.7)%1;dot(im,(lerp(root[0],roots[i+1][0],phase),lerp(root[1],roots[i+1][1],phase)),5,COLORS['yellow'])
        dot(im,root,14,cols[i])
    text(im,(x+w/2,y+5),'cluster roots',22,'#dddddd' if dark else '#425753',anchor='mt')
    text(im,(x+w/2,y+h+10),'particles',22,'#dddddd' if dark else '#425753',anchor='mt')

def chain(im,box,t,dark=True):
    x,y,w,h=box;d=ImageDraw.Draw(im);phase=(t*.7)%4
    if w>500:text(im,(x+w/2,y),'message-passing rounds inside one physical step',24,'#dddddd' if dark else '#425753',anchor='mt')
    for i in range(6):
        px=x+55+i*(w-110)/5;py=y+h*.55+math.sin(i)*30
        if i<5:
            nx=x+55+(i+1)*(w-110)/5;ny=y+h*.55+math.sin(i+1)*30
            arrow(im,(px+16,py),(nx-16,ny),COLORS['gold'],3)
            q=(t*.8-i*.15)%1;dot(im,(lerp(px,nx,q),lerp(py,ny,q)),5,COLORS['yellow'] if dark else '#ad4f39')
        dot(im,(px,py),16,COLORS['blue'] if i==0 else COLORS['red'] if i==5 else COLORS['teal'])
        text(im,(px,py+32),str(i),20,'#dddddd' if dark else '#425753',anchor='mt')
    text(im,(x+w/2,y+h-2),'t stays fixed while information travels' if w>500 else 'one physical step',23,COLORS['yellow'] if dark else '#ad4f39',anchor='mt')

def trajectory(im,box,t,dark=True):
    x,y,w,h=box;cols=[COLORS['blue'],COLORS['teal'],COLORS['gold']]
    for k in range(3):
        cx=x+w*(.16+.34*k);cy=y+h*.55
        for j in range(5):
            for i in range(6):
                px=cx+(i-2.5)*(18+4*k);py=cy+(j-2)*(26-4*k)+math.sin(i*.6+t)*3*k
                dot(im,(px,py),5,cols[k])
        text(im,(cx,y+h-20),['state t','state t + 1','state t + 2'][k],24,'#eeeeee' if dark else '#425753',anchor='mt')
        if k<2:arrow(im,(cx+85,cy),(cx+w*.34-85,cy),cols[k],3)

def control_loop(im,p,style):
    dark=style=='nocturne';fg='#dddddd' if dark else '#395554';accent=COLORS['teal'] if dark else '#9e4b32'
    xs=[270,640,1000];labels=['Execute action','New observation','Predict + optimize']
    phase=min(2,int(p*3))
    for i,(x,label) in enumerate(zip(xs,labels)):
        text(im,(x,530),label,23,accent if i==phase else fg,bold=i==phase,anchor='mt')
        if i<2:arrow(im,(x+125,544),(xs[i+1]-135,544),accent,2)
    d=ImageDraw.Draw(im);d.line([(1000,518),(1000,500),(270,500),(270,518)],fill=accent,width=2)
    arrow(im,(270,500),(270,518),accent,2,7)

def identity(im,style,p):
    dark=style=='nocturne';fg='#ffffff' if dark else '#182d36';accent=COLORS['blue'] if dark else '#9e4b32'
    text(im,(62,45),'DPI-Net',66,accent,serif=style=='atlas',bold=True)
    text(im,(64,126),'ICLR 2019  /  MIT CSAIL',22,fg)
    for i,line in enumerate(['Learning Particle Dynamics for Manipulating','Rigid Bodies, Deformable Objects, and Fluids']):
        text(im,(64,180+43*i),line,33,fg,serif=True)
    text(im,(64,286),'Yunzhu Li · Jiajun Wu · Russ Tedrake',21,fg)
    text(im,(64,319),'Joshua B. Tenenbaum · Antonio Torralba',21,fg)
    if PORTRAIT:
        fit(im,PORTRAIT,(1010,48,175,175))
        text(im,(1097,234),'Yunzhu Li',18,fg,anchor='mt')
    crop_camera(im,(0,0,1852,530),(65,368,1147,205),.96)
    # The original architecture opens every treatment, already legible in context.
    frame_roi(im,(65,368,1212,573),accent,2)

def header(im,idx,style):
    dark=style=='nocturne';fg='#eeeeee' if dark else '#253b41';accent=COLORS['blue'] if dark else '#bb593b' if style=='atlas' else '#176c74'
    text(im,(54,27),'DPI-Net  /  ICLR 2019',17,accent)
    text(im,(54,68),TITLES[idx],36,fg,serif=style=='atlas',bold=style!='atlas')
    text(im,(1227,34),f'{idx+1:02d} / 10',16,accent,anchor='rt')

def nocturne(im,idx,p,t):
    if idx==1:
        graph(im,(260,160,760,330),t,'input')
        text(im,(640,522),'position  x     velocity  v     attributes  a',29,COLORS['blue'],serif=True,anchor='mt')
    elif idx in [2,3]:
        graph(im,(120,155,1040,345),t,'dynamic' if idx==2 else 'local')
        text(im,(640,535),'G(t) changes with the particle configuration' if idx==2 else 'neighbor state → edge message → particle update',27,COLORS['teal'],serif=True,anchor='mt')
    elif idx==4:chain(im,(130,175,1020,330),t)
    elif idx==5:
        hierarchy(im,(180,145,920,340),t)
        text(im,(640,542),'hierarchy for rigid and deformable objects',21,COLORS['teal'],anchor='mt')
    elif idx==6:
        trajectory(im,(120,145,1040,350),t)
        text(im,(640,535),'learned state update, repeated through time',25,COLORS['gold'],anchor='mt')
    elif idx==7:
        crop_camera(im,ROIS[8],(90,175,1100,360),.98)
        x=lerp(350,1020,ease(p));frame_roi(im,(x-85,315,x+85,500),COLORS['gold'],4)
    elif idx==8:
        fit(im,RESULT.crop((60,1000,1815,1220)),(55,205,1170,235))
        text(im,(640,455),'Paper Fig. 4(c): real-world deformable-foam control',21,COLORS['teal'],anchor='mt')
        control_loop(im,p,'nocturne')
    else:
        graph(im,(55,200,360,250),t,'dynamic');chain(im,(455,200,360,250),t);hierarchy(im,(865,180,330,260),t)
        for x,s,c in [(235,'dynamic neighborhoods','blue'),(635,'multi-step messages','gold'),(1030,'hierarchical shortcuts','teal')]:text(im,(x,535),s,22,COLORS[c],anchor='mt')
    if idx in [2,3,4,5] and (p<.28 or p>.86):
        # Each mathematical construction emerges directly from its paper panel.
        plate=Image.new('RGB',(W,H),'#000000')
        focused_figure(plate,ROIS[idx],(100,145,1080,410),.92+.08*ease(p/.28))
        alpha=1-ease((p-.12)/.16) if p<.28 else ease((p-.86)/.14)
        im.paste(Image.blend(im,plate,alpha).crop((70,140,1210,560)),(70,140))

def microscope(im,idx,p,t):
    # Continuous framing from the previous named source region to the new one.
    prev=ROIS[max(0,idx-1)];target=ROIS[idx];u=ease(p/.25)
    roi=tuple(lerp(a,b,u) for a,b in zip(prev,target))
    if idx==8:
        fit(im,RESULT.crop((60,1000,1815,1220)),(45,180,1190,275))
        frame_roi(im,(74+min(p,.9)*1050,215,200+min(p,.9)*1050,435),'#c36435',3)
        control_loop(im,p,'microscope')
        return
    mapper=focused_figure(im,roi,(60,145,1160,390),lerp(.92,1.02,ease(p)))
    labels=['','INPUT / particle state','DYNAMIC GRAPH / neighborhood changes','LOCAL / pairwise messages','MULTI-STEP / effects travel farther','HIERARCHY / rigid and deformable objects','OUTPUT / predicted particle state','CONTROL / differentiate target error','','THE COMPLETE METHOD / Figure 1']
    text(im,(62,552),labels[idx],22,'#176c74')
    targets={1:(1090,640,1290,810),2:(110,30,800,395),3:(930,180,1360,470),4:(500,650,850,830),5:(1380,5,1840,470),6:(1280,620,1580,820),7:(1290,610,1840,825),9:(0,0,1852,860)}
    if idx in targets:
        l,q,r,b=targets[idx];a=mapper((l,q));c=mapper((r,b));frame_roi(im,(*a,*c),'#c76d32',3)
    paths={3:[(1310,220),(1280,290),(1210,290)],4:[(520,690),(590,745),(670,700),(725,775),(810,800)],5:[(1410,435),(1470,175),(1555,35),(1710,35),(1720,290)],7:[(1790,730),(1600,730),(1475,630),(1300,630),(1300,690)]}
    if idx in paths:
        path=paths[idx];phase=(p*2)%1;seg=min(len(path)-2,int(phase*(len(path)-1)));q=phase*(len(path)-1)-seg
        pos=mapper((lerp(path[seg][0],path[seg+1][0],q),lerp(path[seg][1],path[seg+1][1],q)))
        dot(im,pos,8,'#eb8d36')

def atlas(im,idx,p,t):
    # A spatially continuous field; the camera travels between large, unboxed islands.
    # The original figures and generated explanations inhabit the same world plane.
    world=Image.new('RGB',(3100,1500),'#f5f0e6');d=ImageDraw.Draw(world)
    for x in range(20,3100,50):
        for y in range(20,1500,50):dot(world,(x,y),1,'#d8d4c6')
    text(world,(80,80),'01  STATE',65,'#1e4e55',serif=True)
    fit(world,PAPER.crop((910,640,1270,850)),(80,185,500,300))
    text(world,(840,80),'02  RELATIONS',65,'#a45239',serif=True)
    graph(world,(820,195,650,310),t,'dynamic',False)
    text(world,(1730,80),'03  PROPAGATE',65,'#846b27',serif=True)
    chain(world,(1680,190,750,320),t,False)
    text(world,(1740,750),'04  HIERARCHY',65,'#1e6c63',serif=True)
    hierarchy(world,(1710,860,800,320),t,False)
    text(world,(850,750),'05  FUTURE',65,'#3d5c74',serif=True)
    trajectory(world,(780,860,760,350),t,False)
    text(world,(80,750),'06  CONTROL',65,'#a45239',serif=True)
    fit(world,PAPER.crop((910,540,1852,860)),(55,870,670,330))
    for a,b in [((600,325),(800,325)),((1495,325),(1650,325)),((2110,540),(2110,690)),((1690,1080),(1580,1080)),((800,1080),(750,1080))]:arrow(world,a,b,'#b7a78b',6,19)
    cams=[(0,0,2500,1300),(20,20,800,520),(750,10,850,530),(750,100,850,530),(1620,30,900,540),(1630,720,930,550),(750,720,900,550),(0,700,850,560),(0,700,850,560),(0,0,2600,1300)]
    a=cams[max(0,idx-1)];b=cams[idx];u=ease(min(1,p/.23))
    cx,cy,cw,ch=[lerp(q,r,u) for q,r in zip(a,b)]
    # Fit the virtual view into the content area without aspect distortion.
    target=(55,140,1170,430)
    crop=world.crop((int(cx),int(cy),int(cx+cw),int(cy+ch)))
    fit(im,crop,target)
    if idx==8:
        ImageDraw.Draw(im).rectangle((55,140,1225,570),fill='#f5f0e6')
        text(im,(640,155),'06  CONTROL',44,'#a45239',serif=True,anchor='mt')
        fit(im,PAPER.crop((910,540,1852,860)),(290,207,700,145))
        fit(im,RESULT.crop((70,1020,1470,1205)),(195,350,900,130))
        control_loop(im,p,'atlas')
    if idx==9:text(im,(640,560),'A changing graph is the computational model of interaction.',22,'#1e4e55',serif=True,anchor='mt')

def render_frame(t,style,subs=True):
    idx=next((i for i,s in enumerate(SCRIPT['sentences']) if s['start']<=t<s['end']),9)
    sent=SCRIPT['sentences'][idx];p=(t-sent['start'])/(sent['end']-sent['start'])
    bg={'nocturne':'#000000','microscope':'#ffffff','atlas':'#f5f0e6'}[style]
    im=Image.new('RGB',(W,H),bg)
    if idx==0:identity(im,style,p)
    else:
        header(im,idx,style)
        {'nocturne':nocturne,'microscope':microscope,'atlas':atlas}[style](im,idx,p,t)
    panel={0:'Fig. 1',1:'Fig. 1(d)',2:'Fig. 1(a)',3:'Fig. 1(b)',4:'Fig. 1(c)',5:'Fig. 1(b)',6:'Fig. 1(d)',7:'Fig. 1(d)',8:'Fig. 4(c)',9:'Fig. 1'}[idx]
    original=idx==0 or style=='microscope' or (style=='nocturne' and (idx in [7,8] or (idx in [2,3,4,5] and (p<.12 or p>.99)))) or (style=='atlas' and idx in [1,7,8])
    caption=f'Li et al., ICLR 2019 · {panel}' if original else 'Conceptual illustration'
    if style=='atlas' and idx==9:caption='Conceptual route · paper excerpts: Li et al., Fig. 1'
    text(im,(18,581),caption,12,'#999999' if style=='nocturne' else '#67787c')
    if subs:subtitles(im,sent)
    return im

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--style',choices=['all','nocturne','microscope','atlas'],default='all')
    parser.add_argument('--stills',action='store_true');parser.add_argument('--start',type=float,default=0);parser.add_argument('--end',type=float);parser.add_argument('--no-subs',action='store_true');parser.add_argument('--fps',type=int,default=24);parser.add_argument('--ffmpeg',default=os.environ.get('FFMPEG_BINARY',shutil.which('ffmpeg') or str(Path(sys.prefix)/'Library/bin/ffmpeg.exe')))
    args=parser.parse_args();styles=['nocturne','microscope','atlas'] if args.style=='all' else [args.style]
    (ROOT/'renders').mkdir(exist_ok=True);(ROOT/'qa').mkdir(exist_ok=True)
    for style in styles:
        if args.stills:
            for i,s in enumerate(SCRIPT['sentences']):
                render_frame((s['start']+s['end'])/2,style,not args.no_subs).save(ROOT/'qa'/f'{style}_{i:02}.jpg',quality=94)
            print(f'{style}: QA frames written',flush=True);continue
        end=args.end or SCRIPT['duration'];frames=round((end-args.start)*args.fps)
        path=ROOT/'renders'/f'{style}{"_excerpt" if args.start or args.end else ""}.mp4'
        cmd=[args.ffmpeg,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(args.fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
        with open(ROOT/'qa'/f'{style}-encode.log','w') as log:
            proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log,creationflags=0x08000000 if os.name=='nt' else 0)
            for frame in range(frames):
                proc.stdin.write(render_frame(args.start+frame/args.fps,style,not args.no_subs).tobytes())
                if frame%240==0:print(f'{style} {frame}/{frames}',flush=True)
            proc.stdin.close();code=proc.wait()
            if code:raise RuntimeError(f'FFmpeg failed: {code}')
        print(f'DONE {path}',flush=True)

if __name__=='__main__':main()
