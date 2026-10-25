"""Native 1080p/60 paper animation with a persistent figure locator.

Assets and the original project are supplied explicitly. No private paths are
stored in this renderer. Generated particle motion is a teaching schematic.
"""
from pathlib import Path
import argparse, json, math, os, subprocess
from PIL import Image, ImageDraw, ImageFont

S=1.5; W,H=1920,1080
BG='#151515'; FG='#eeeeec'; MUTED='#a6a6a2'
BLUE='#58c4dd'; TEAL='#5cd0b3'; GOLD='#f0c564'; RED='#ef5965'
FONTDIR=Path(os.environ.get('FONT_DIR',str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts')))
FONTS={}

def ease(x):
    x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))
def lerp(a,b,p):return a+(b-a)*p
def blendcolor(a,b,p):
    a=tuple(int(a[i:i+2],16) for i in (1,3,5));b=tuple(int(b[i:i+2],16) for i in (1,3,5))
    return tuple(round(lerp(x,y,p)) for x,y in zip(a,b))
def font(size,bold=False):
    key=(size,bold)
    if key not in FONTS:FONTS[key]=ImageFont.truetype(str(FONTDIR/('msyhbd.ttc' if bold else 'msyh.ttc')),round(size*S))
    return FONTS[key]

class Canvas:
    def __init__(self):self.im=Image.new('RGB',(W,H),BG);self.d=ImageDraw.Draw(self.im)
    def line(self,pts,color=MUTED,width=2):self.d.line([(x*S,y*S) for x,y in pts],fill=color,width=max(1,round(width*S)))
    def rect(self,box,color=None,outline=None,width=1,radius=0):
        f=self.d.rounded_rectangle if radius else self.d.rectangle
        kw={'radius':radius*S} if radius else {}
        f(tuple(v*S for v in box),fill=color,outline=outline,width=max(1,round(width*S)),**kw)
    def circle(self,p,r=7,color=BLUE,outline=None,width=1):
        x,y=p;self.d.ellipse(((x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S),fill=color,outline=outline,width=max(1,round(width*S)))
    def text(self,xy,s,size=24,color=FG,bold=False,anchor=None):self.d.text((xy[0]*S,xy[1]*S),s,font=font(size,bold),fill=color,anchor=anchor)
    def arrow(self,a,b,color=TEAL,width=2,head=9):
        self.line([a,b],color,width);ang=math.atan2(b[1]-a[1],b[0]-a[0])
        pts=[b,(b[0]-head*math.cos(ang-.45),b[1]-head*math.sin(ang-.45)),(b[0]-head*math.cos(ang+.45),b[1]-head*math.sin(ang+.45))]
        self.d.polygon([(x*S,y*S) for x,y in pts],fill=color)
    def fit(self,src,box):
        x,y,w,h=box;z=min(w/src.width,h/src.height);nw,nh=round(src.width*z*S),round(src.height*z*S)
        self.im.paste(src.resize((nw,nh),Image.Resampling.LANCZOS),(round((x+w/2)*S-nw/2),round((y+h/2)*S-nh/2)))
    def crop(self,src,roi,box):
        # One affine sample uses floating-point coordinates throughout the camera.
        x,y,w,h=box;l,t,r,b=roi;z=min(w/(r-l),h/(b-t))*S;cx=(l+r)/2;cy=(t+b)/2
        dst=(round(w*S),round(h*S));coeff=(1/z,0,cx-dst[0]/(2*z),0,1/z,cy-dst[1]/(2*z))
        view=src.transform(dst,Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC,fillcolor='white')
        self.im.paste(view,(round(x*S),round(y*S)))

ROIS=[(0,0,1852,860),(910,635,1285,855),(20,10,900,500),(905,0,1380,520),(10,535,895,855),(1375,0,1850,520),(1280,625,1590,855),(1290,540,1850,855),(905,535,1850,855),(0,0,1852,860)]
MODULES=['Complete method','Particle state · Fig. 1(d)','Dynamic graph · Fig. 1(a)','Local propagation · Fig. 1(b)','Multi-step effects · Fig. 1(c)','Hierarchy · Fig. 1(b)','Prediction · Fig. 1(d)','Optimization · Fig. 1(d)','Observe and replan · Fig. 1(d)','Complete method']
TITLES=['Learning to predict particle motion','Start with a particle state','Rebuild the interaction graph','Exchange messages with neighbors','Pass effects across several hops','Use hierarchy to reach distant parts','Roll the model forward','Optimize an action through the model','Execute, observe, and replan','Three mechanisms, one learned simulator']

def overview(c,paper,idx,elapsed):
    x,y,w=860,100,370;h=w*paper.height/paper.width
    c.text((x,y-33),'ORIGINAL METHOD',15,MUTED)
    c.fit(paper,(x,y,w,h))
    prev=ROIS[max(0,idx-1)];dest=ROIS[idx];u=ease(elapsed/.85)
    roi=[lerp(a,b,u) for a,b in zip(prev,dest)]
    l,t,r,b=roi;z=w/paper.width
    c.rect((x+l*z,y+t*z,x+r*z,y+b*z),outline=RED,width=2.4,radius=2)
    c.text((x,y+h+15),MODULES[idx],15,RED)
    c.text((x,y+h+42),'Li et al. · ICLR 2019 · Figure 1',12,MUTED)

def draw_graph(c,t,mode):
    pts=[]
    for j in range(4):
        for i in range(7):
            x=90+i*110+math.sin(t*.5+j*1.1+i*.6)*17
            y=200+j*78+math.cos(t*.6+i*1.4+j)*13
            pts.append((x,y))
    links=[]
    for a in range(len(pts)):
        for b in range(a+1,len(pts)):
            dist=math.dist(pts[a],pts[b]);alpha=1-ease((dist-108)/34)
            if alpha>0:
                links.append((a,b));c.line([pts[a],pts[b]],blendcolor(BG,'#596064',alpha),1.6)
    if mode=='local':
        focus=10
        for a,b in links:
            if a==focus or b==focus:
                source=b if a==focus else a;u=(t*.6+source*.073)%1
                c.line([pts[source],pts[focus]],TEAL,2)
                c.circle((lerp(pts[source][0],pts[focus][0],u),lerp(pts[source][1],pts[focus][1],u)),4,GOLD)
        c.circle(pts[focus],21,None,TEAL,1.5)
    for k,p in enumerate(pts):c.circle(p,7.5,[BLUE,TEAL,GOLD,'#c7c7c1'][k%4])
    if mode=='input':
        p=pts[10];c.circle(p,24,None,GOLD,1.8);c.arrow(p,(p[0]+60,p[1]-40),GOLD)
        c.text((60,510),'position  x    velocity  v    attributes  a',27,BLUE)
    elif mode=='local':c.text((60,510),'neighbor state  →  message  →  particle update',25,TEAL)
    else:c.text((60,510),'Edges follow proximity as particles move.',25,TEAL)

def draw_chain(c,elapsed):
    pts=[(95+i*135,305+math.sin(i*.8)*32) for i in range(6)]
    progress=min(5,elapsed*1.25)
    for i in range(5):
        c.arrow((pts[i][0]+18,pts[i][1]),(pts[i+1][0]-18,pts[i+1][1]),'#555856',2)
        if progress>i:
            u=min(1,progress-i);c.line([pts[i],(lerp(pts[i][0],pts[i+1][0],u),lerp(pts[i][1],pts[i+1][1],u))],GOLD,3)
            c.circle((lerp(pts[i][0],pts[i+1][0],u),lerp(pts[i][1],pts[i+1][1],u)),5,GOLD)
    for i,p in enumerate(pts):
        c.circle(p,15,GOLD if i<=progress else '#515352');c.text((p[0],p[1]+34),f'particle {i}',15,MUTED,anchor='mt')
    c.text((60,195),'Propagation round',22,MUTED);c.text((60,230),str(min(5,int(progress)+1)),44,GOLD,bold=True)
    c.text((60,510),'Information travels while physical time stays at t.',24,TEAL)

def draw_hierarchy(c,elapsed,duration):
    roots=[(155+i*205,225+(-1)**i*12) for i in range(4)]
    cols=[BLUE,TEAL,GOLD,'#d698cb'];phase=min(2,int(elapsed/duration*3));u=(elapsed/duration*3)%1
    labels=['particles → cluster roots','root → root','cluster roots → particles']
    for i,root in enumerate(roots):
        if i<3:
            c.line([root,roots[i+1]],'#505854',2)
            if phase==1:
                c.arrow(root,roots[i+1],GOLD,2);c.circle((lerp(root[0],roots[i+1][0],u),lerp(root[1],roots[i+1][1],u)),5,GOLD)
        for j in range(5):
            p=(75+i*205+j*35,410+math.sin(j+i)*20);c.line([p,root],'#414744',1.5);c.circle(p,6,cols[i])
            if phase in [0,2]:
                v=u if phase==0 else 1-u;c.circle((lerp(p[0],root[0],v),lerp(p[1],root[1],v)),4,cols[i])
        c.circle(root,14,cols[i])
    c.text((60,155),labels[phase],24,TEAL)
    c.text((60,510),'A shorter route across a rigid or deformable object.',23,MUTED)

def draw_trajectory(c,t):
    for k in range(3):
        x=175+k*265;y=310
        for j in range(5):
            for i in range(6):
                px=x+(i-2.5)*(17+4*k);py=y+(j-2)*(27-4*k)+math.sin(i*.6+t*.6)*3*k
                c.circle((px,py),5,[BLUE,TEAL,GOLD][k])
        c.text((x,440),['state t','state t + 1','state t + 2'][k],23,[BLUE,TEAL,GOLD][k],anchor='mt')
        if k<2:c.arrow((x+80,y),(x+180,y),TEAL,2)
    c.text((60,510),'The same learned update is applied repeatedly.',24,MUTED)

def draw_control(c,paper,idx,p):
    c.crop(paper,(902,535,1852,860),(55,175,760,267))
    if idx==7:
        steps=['candidate action','predicted state','target error','gradient to action']
        k=min(3,int(p*4));c.text((60,495),steps[k],28,[BLUE,TEAL,GOLD,RED][k])
        c.text((60,542),'Prediction and optimization share the learned model.',21,MUTED)
    else:
        xs=[150,435,725]
        for i,(x,txt) in enumerate(zip(xs,['Execute','Observe','Replan'])):
            c.text((x,500),txt,25,TEAL if i==min(2,int(p*3)) else MUTED,anchor='mt')
            if i<2:c.arrow((x+65,518),(xs[i+1]-67,518),TEAL)

def wrap(s,size,width):
    words=s.split(' ') if ' ' in s and not any('\u4e00'<=x<='\u9fff' for x in s) else list(s)
    sep=' ' if words!=list(s) else '';rows=[];line=''
    for word in words:
        candidate=line+sep+word if line else word
        if font(size).getlength(candidate)>width*S and line:rows.append(line);line=word
        else:line=candidate
    if line:rows.append(line)
    return rows

def subtitle(c,s):
    c.rect((0,600,1280,720),'#0c0c0c');zh=wrap(s['zh'],23,1160);en=wrap(s['en'],18,1160)
    zh_h=len(zh)*30;en_h=len(en)*25;top=600+(120-zh_h-en_h-5)/2
    for line in zh:c.text((640,top),line,23,FG,anchor='mt');top+=30
    top+=5
    for line in en:c.text((640,top),line,18,'#c8c8c4',anchor='mt');top+=25

def render(t,script,paper,portrait):
    idx=next((i for i,s in enumerate(script['sentences']) if s['start']<=t<s['end']),9)
    sent=script['sentences'][idx];elapsed=t-sent['start'];dur=sent['end']-sent['start'];p=elapsed/dur
    c=Canvas();c.text((55,26),'DPI-Net  /  ICLR 2019',16,TEAL)
    if idx:
        c.text((55,71),TITLES[idx],31,FG,bold=True)
    else:
        c.text((55,86),'DPI-Net',55,BLUE,bold=True)
        c.text((56,167),'Learning Particle Dynamics for Manipulating',26,FG)
        c.text((56,206),'Rigid Bodies, Deformable Objects, and Fluids',26,FG)
        c.text((57,263),'MIT CSAIL · ICLR 2019',21,TEAL)
        c.fit(paper,(55,318,735,250))
        if portrait is not None:c.fit(portrait,(945,365,125,125))
        c.text((1008,505),'Yunzhu Li',18,FG,anchor='mt')
        c.text((1008,535),'with Wu, Tedrake, Tenenbaum, Torralba',12,MUTED,anchor='mt')
    overview(c,paper,idx,elapsed)
    if idx in [1,2,3]:draw_graph(c,t,['','input','dynamic','local'][idx])
    elif idx==4:draw_chain(c,elapsed)
    elif idx==5:draw_hierarchy(c,elapsed,dur)
    elif idx==6:draw_trajectory(c,t)
    elif idx in [7,8]:draw_control(c,paper,idx,p)
    elif idx==9:
        labels=[('Dynamic neighborhoods','Follow the moving configuration',BLUE),('Multi-step propagation','Carry effects across local edges',GOLD),('Hierarchical propagation','Connect distant parts of an object',TEAL)]
        for i,(name,desc,color) in enumerate(labels):
            y=190+i*118;c.circle((77,y+18),7,color);c.text((105,y),name,28,color);c.text((105,y+43),desc,21,MUTED)
    if idx not in [0,7,8]:c.text((55,576),'Particle motion: teaching schematic',12,MUTED)
    elif idx in [7,8]:c.text((55,576),'Original method: Li et al., ICLR 2019, Figure 1(d)',12,MUTED)
    subtitle(c,sent);return c.im

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--assets',type=Path,required=True);ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--ffmpeg',type=Path,required=True);ap.add_argument('--fps',type=int,default=60);ap.add_argument('--stills',action='store_true')
    args=ap.parse_args();out=args.output;script=json.loads((out/'script.timed.json').read_text(encoding='utf-8'))
    paper=Image.open(args.assets/'dpi_net_method.png').convert('RGB');portrait_path=args.assets/'yunzhu-li.jpg'
    portrait=Image.open(portrait_path).convert('RGB') if portrait_path.exists() else None
    qa=out/'qa';qa.mkdir(exist_ok=True)
    for i,s in enumerate(script['sentences']):render((s['start']+s['end'])/2,script,paper,portrait).save(qa/f'scene-{i:02}.jpg',quality=93)
    if args.stills:return
    frames=round(script['duration']*args.fps);dest=out/'DPI_A_persistent_map_110.mp4'
    cmd=[str(args.ffmpeg),'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(args.fps),'-i','-','-i',str(out/'mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','18','-c:a','aac','-b:a','192k','-pix_fmt','yuv420p','-t',str(script['duration']),'-movflags','+faststart',str(dest)]
    with open(qa/'encode.log','w') as log:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log,creationflags=0x08000000 if os.name=='nt' else 0)
        for n in range(frames):
            proc.stdin.write(render(n/args.fps,script,paper,portrait).tobytes())
            if n%300==0:print(f'{n}/{frames}',flush=True)
        proc.stdin.close();code=proc.wait()
    if code:raise RuntimeError('FFmpeg failed; see qa/encode.log')
    print(f'DONE {dest}',flush=True)

if __name__=='__main__':main()
