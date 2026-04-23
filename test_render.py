import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import math, time, random

# ═══════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════
def box(cx,cy,cz,sx,sy,sz,r,g,b):
    glColor3f(r,g,b)
    hx,hy,hz=sx/2,sy/2,sz/2
    glPushMatrix(); glTranslatef(cx,cy,cz)
    glBegin(GL_QUADS)
    glNormal3f(0,1,0);  glVertex3f(-hx,hy,-hz);glVertex3f(hx,hy,-hz);glVertex3f(hx,hy,hz);glVertex3f(-hx,hy,hz)
    glNormal3f(0,-1,0); glVertex3f(-hx,-hy,hz);glVertex3f(hx,-hy,hz);glVertex3f(hx,-hy,-hz);glVertex3f(-hx,-hy,-hz)
    glNormal3f(0,0,1);  glVertex3f(-hx,-hy,hz);glVertex3f(hx,-hy,hz);glVertex3f(hx,hy,hz);glVertex3f(-hx,hy,hz)
    glNormal3f(0,0,-1); glVertex3f(-hx,hy,-hz);glVertex3f(hx,hy,-hz);glVertex3f(hx,-hy,-hz);glVertex3f(-hx,-hy,-hz)
    glNormal3f(-1,0,0); glVertex3f(-hx,-hy,-hz);glVertex3f(-hx,-hy,hz);glVertex3f(-hx,hy,hz);glVertex3f(-hx,hy,-hz)
    glNormal3f(1,0,0);  glVertex3f(hx,-hy,hz);glVertex3f(hx,-hy,-hz);glVertex3f(hx,hy,-hz);glVertex3f(hx,hy,hz)
    glEnd(); glPopMatrix()

def silinder(cx,cy,cz,r,h,sl=10,cr=0.5,cg=0.5,cb=0.5):
    glColor3f(cr,cg,cb); glPushMatrix(); glTranslatef(cx,cy,cz)
    q=gluNewQuadric(); gluCylinder(q,r,r,h,sl,1)
    gluDisk(q,0,r,sl,1); glTranslatef(0,0,h); gluDisk(q,0,r,sl,1)
    gluDeleteQuadric(q); glPopMatrix()

def kerucut(cx,cy,cz,base,h,sl=8,cr=0.5,cg=0.5,cb=0.5):
    glColor3f(cr,cg,cb); glPushMatrix(); glTranslatef(cx,cy,cz)
    q=gluNewQuadric(); gluCylinder(q,base,0,h,sl,1)
    gluDisk(q,0,base,sl,1); gluDeleteQuadric(q); glPopMatrix()

def bola(cx,cy,cz,r,sl=10,st=10,cr=1,cg=1,cb=1):
    glColor3f(cr,cg,cb); glPushMatrix(); glTranslatef(cx,cy,cz)
    q=gluNewQuadric(); gluSphere(q,r,sl,st)
    gluDeleteQuadric(q); glPopMatrix()

def lerp(a,b,t): return a+(b-a)*max(0.0,min(1.0,t))

# ═══════════════════════════════════════════════
#  JALAN & LINGKUNGAN
# ═══════════════════════════════════════════════
def draw_pohon(x,z):
    glPushMatrix(); glTranslatef(x,0,z)
    glColor3f(0.35,0.20,0.08)
    q=gluNewQuadric(); gluCylinder(q,0.18,0.12,1.8,7,1)
    glColor3f(0.18,0.50,0.15)
    glTranslatef(0,1.5,0); gluCylinder(q,0.0,1.1,1.4,9,1)
    glTranslatef(0,0.8,0); gluCylinder(q,0.0,0.9,1.2,9,1)
    glTranslatef(0,0.7,0); gluCylinder(q,0.0,0.65,1.0,9,1)
    gluDeleteQuadric(q); glPopMatrix()

def draw_jalan():
    box(0,-0.05,0,100,0.1,60,0.25,0.45,0.18)
    box(0,0.02,0,100,0.04,3.5,0.48,0.46,0.44)
    box(0,0.03,0,8.0,0.06,60,0.20,0.20,0.22)
    for i in range(-14,15):
        zi=i*2.0
        if abs(zi)<2.5: continue
        box(0,0.07,zi,0.15,0.01,1.0,0.9,0.9,0.9)
    box(0,0.03,-4.5,8.0,0.05,1.0,0.16,0.16,0.18)
    box(0,0.03, 4.5,8.0,0.05,1.0,0.16,0.16,0.18)
    for zi in [-22,-16,-11,-7,7,11,16,22]:
        draw_pohon(-6.0,zi); draw_pohon(6.0,zi)

# ═══════════════════════════════════════════════
#  REL
# ═══════════════════════════════════════════════
def draw_rel():
    for i in range(-27,28):
        box(i*1.5,0.05,0,1.2,0.12,1.8,0.40,0.25,0.10)
    box(0,0.18,-0.7,80,0.1,0.15,0.6,0.6,0.65)
    box(0,0.24,-0.7,80,0.05,0.22,0.7,0.7,0.75)
    box(0,0.18, 0.7,80,0.1,0.15,0.6,0.6,0.65)
    box(0,0.24, 0.7,80,0.05,0.22,0.7,0.7,0.75)

# ═══════════════════════════════════════════════
#  PORTAL
# ═══════════════════════════════════════════════
def draw_satu_palang(x,z,sudut):
    glPushMatrix(); glTranslatef(x,0,z)
    silinder(0,0,0,0.12,2.0,8,0.2,0.2,0.2)
    box(0,2.15,0,0.4,0.3,0.4,0.15,0.15,0.15)
    glTranslatef(0,2.15,0); glRotatef(sudut,0,0,1)
    for i in range(8):
        px=i*0.5+0.25
        if i%2==0: box(px,0,0,0.48,0.12,0.12,0.9,0.1,0.1)
        else:      box(px,0,0,0.48,0.12,0.12,0.95,0.95,0.95)
    bola(4.15,0,0,0.18,cr=0.9,cg=0.1,cb=0.1)
    glPopMatrix()

def draw_lampu(x,z,merah):
    silinder(x,0,z,0.08,3.5,8,0.2,0.2,0.2)
    box(x,3.7,z,0.5,0.9,0.3,0.1,0.1,0.1)
    if merah: bola(x,4.0,z+0.05,0.16,cr=1.0,cg=0.0,cb=0.0)
    else:         bola(x,4.0,z+0.05,0.16,cr=0.3,cg=0.0,cb=0.0)
    if not merah: bola(x,3.45,z+0.05,0.16,cr=0.0,cg=1.0,cb=0.0)
    else:         bola(x,3.45,z+0.05,0.16,cr=0.0,cg=0.25,cb=0.0)

def draw_pos_jaga():
    box(5.5,0.15,0,2.2,0.3,2.2,0.4,0.35,0.28)  
    box(5.5,1.65,0,2.4,0.15,2.4,0.55,0.28,0.18)
    box(5.5,0.95,1.05,1.0,0.5,0.05,0.6,0.82,0.9)
    box(5.5,0.65,-1.0,0.7,0.8,0.05,0.5,0.35,0.2)

def draw_portal(sudut,merah):
    draw_satu_palang(-1.5,-2.5, sudut)
    draw_satu_palang(-1.5, 2.5,-sudut)
    draw_lampu(2.5,-5.0,merah)
    draw_lampu(2.5, 5.0,merah)
    draw_pos_jaga()

# ═══════════════════════════════════════════════
#  KERETA
# ═══════════════════════════════════════════════
def draw_roda(cx,cy,cz):
    silinder(cx,cy,cz-0.7,0.08,1.4,8,0.3,0.3,0.3)
    for oz in [-0.7,0.7]:
        glPushMatrix(); glTranslatef(cx,cy,oz)
        glRotatef(90,1,0,0); glColor3f(0.15,0.15,0.15)
        q=gluNewQuadric(); gluCylinder(q,0.35,0.35,0.12,14,1)
        gluDisk(q,0,0.35,14,1); glTranslatef(0,0,0.12)
        gluDisk(q,0,0.35,14,1); gluDeleteQuadric(q); glPopMatrix()

def draw_lokomotif(ox):
    glPushMatrix(); glTranslatef(ox,0,0)
    box(0,0.6,0,5.5,0.7,1.7,0.12,0.12,0.12)
    box(0.3,1.25,0,4.5,0.9,1.65,0.85,0.12,0.12)
    box(-1.5,1.8,0,1.8,0.75,1.6,0.75,0.10,0.10)
    box(-1.5,1.95,0.7,1.6,0.5,0.05,0.6,0.85,0.95)
    box(-1.5,1.95,-0.7,1.6,0.5,0.05,0.6,0.85,0.95)
    box(2.2,0.95,0,1.2,0.55,1.65,0.7,0.10,0.10)
    box(2.82,1.1,0.5,0.05,0.2,0.2,1.0,1.0,0.7)
    box(2.82,1.1,-0.5,0.05,0.2,0.2,1.0,1.0,0.7)
    silinder(-0.5,2.15,0,0.18,0.45,8,0.1,0.1,0.1)
    draw_roda(-1.5,0.35,0); draw_roda(0.0,0.35,0); draw_roda(1.5,0.35,0)
    glPopMatrix()

def draw_gerbong(ox,r=0.15,g=0.45,b=0.70):
    glPushMatrix(); glTranslatef(ox,0,0)
    box(0,0.6,0,5.0,0.65,1.7,0.12,0.12,0.12)
    box(0,1.28,0,5.0,0.95,1.65,r,g,b)
    box(0,1.85,0,4.8,0.2,1.6,r*0.75,g*0.75,b*0.75)
    for jx in [-1.6,-0.4,0.8,2.0]:
        box(jx,1.35,0.84,0.9,0.38,0.03,0.8,0.9,0.95)
        box(jx,1.35,-0.84,0.9,0.38,0.03,0.8,0.9,0.95)
    draw_roda(-1.2,0.35,0); draw_roda(1.2,0.35,0)
    glPopMatrix()

def draw_kereta(px):
    draw_lokomotif(px)
    for i in range(4):
        draw_gerbong(px-5.8-i*5.6)

# ═══════════════════════════════════════════════
#  KENDARAAN
# ═══════════════════════════════════════════════
WARNA=[(0.8,0.12,0.12),(0.15,0.35,0.78),(0.88,0.75,0.10),
       (0.9,0.9,0.9),(0.12,0.12,0.12),(0.15,0.55,0.20),(0.8,0.45,0.10)]

def draw_roda_k(x,y,z,r=0.28):
    glPushMatrix(); glTranslatef(x,y,z); glRotatef(90,1,0,0)
    glColor3f(0.12,0.12,0.12)
    q=gluNewQuadric(); gluCylinder(q,r,r,0.15,10,1)
    gluDisk(q,0,r,10,1); glTranslatef(0,0,0.15); gluDisk(q,0,r,10,1)
    gluDeleteQuadric(q); glPopMatrix()

def draw_mobil(x,z,wi=0):
    r,g,b=WARNA[wi%len(WARNA)]
    glPushMatrix(); glTranslatef(x,0,z)
    box(0,0.32,0,1.0,0.52,2.2,r*0.85,g*0.85,b*0.85)
    box(0,0.82,0.1,0.9,0.45,1.35,r,g,b)
    box(0,0.85,0.82,0.85,0.35,0.04,0.6,0.82,0.92)
    box(0,0.85,-0.72,0.85,0.30,0.04,0.6,0.82,0.92)
    box(0.38,0.38,1.11,0.18,0.12,0.04,1.0,1.0,0.8)
    box(-0.38,0.38,1.11,0.18,0.12,0.04,1.0,1.0,0.8)
    draw_roda_k(0.52,0.25,0.75); draw_roda_k(-0.52,0.25,0.75)
    draw_roda_k(0.52,0.25,-0.75); draw_roda_k(-0.52,0.25,-0.75)
    glPopMatrix()

def draw_motor(x,z,wi=0):
    r,g,b=WARNA[wi%len(WARNA)]
    glPushMatrix(); glTranslatef(x,0,z)
    box(0,0.45,0,0.45,0.35,1.2,r,g,b)
    box(0,0.82,0.45,0.75,0.08,0.08,0.3,0.3,0.3)
    box(0,0.68,-0.1,0.38,0.12,0.65,0.1,0.1,0.1)
    draw_roda_k(0.12,0.22,0.5,0.22); draw_roda_k(-0.12,0.22,0.5,0.22)
    draw_roda_k(0.12,0.22,-0.5,0.22); draw_roda_k(-0.12,0.22,-0.5,0.22)
    glPopMatrix()

class Kendaraan:
    def __init__(self,z,x,tipe,warna):
        self.z=z; self.x=x; self.tipe=tipe; self.warna=warna
        self.arah=1 if z<0 else -1
        self.speed=4.5 if tipe=='motor' else 3.5
        self.batas=3.5*self.arah
    def update(self,dt,tutup):
        if tutup:
            if self.arah==1 and self.z < 4.0:
                self.z+=self.speed*dt
            elif self.arah==-1 and self.z > -4.0:
                self.z-=self.speed*dt
        else:
            self.z+=self.arah*self.speed*dt
            if self.z>28: self.z=-28
            if self.z<-28: self.z=28
    def draw(self):
        glPushMatrix(); glTranslatef(self.x,0,self.z)
        if self.arah==-1: glRotatef(180,0,1,0)
        glTranslatef(-self.x,0,-self.z)
        if self.tipe=='mobil': draw_mobil(self.x,self.z,self.warna)
        else: draw_motor(self.x,self.z,self.warna)
        glPopMatrix()

def buat_kendaraan():
    kd=[]
    data=[(-22,-1.5,'mobil',0),(-15,-1.5,'motor',2),(-8,-1.5,'mobil',4),
          (-2,-1.5,'mobil',1),(10,-1.5,'motor',3),(18,-1.5,'mobil',6),
          (22,1.5,'mobil',5),(15,1.5,'motor',1),(8,1.5,'mobil',2),
          (3,1.5,'motor',0),(-10,1.5,'mobil',3),(-18,1.5,'mobil',6)]
    for z,x,t,w in data: kd.append(Kendaraan(z,x,t,w))
    return kd

# ═══════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════
fase=0; ftimer=0.0
kereta_x=55.0; palang=90.0; merah=False
kendaraan=buat_kendaraan()
yaw=45.0; pitch=35.0; dist=25.0
mx=0.0; my=0.0; mdown=False

def update(dt):
    global fase,ftimer,kereta_x,palang,merah
    ftimer+=dt
    if fase==0:
        merah=False; palang=90.0; kereta_x=55.0
        if ftimer>5.0: fase=1; ftimer=0.0
    elif fase==1:
        merah=True; palang=lerp(90.0,0.0,ftimer/2.5)
        if ftimer>2.5: fase=2; ftimer=0.0; palang=0.0
    elif fase==2:
        merah=True; palang=0.0; kereta_x-=14.0*dt
        if ftimer>5.5: fase=3; ftimer=0.0
    elif fase==3:
        merah=True; palang=lerp(0.0,90.0,ftimer/2.0)
        if ftimer>2.0: fase=0; ftimer=0.0; merah=False; palang=90.0; kereta_x=55.0
    for k in kendaraan: k.update(dt,fase in(1,2,3))

def main():
    global yaw,pitch,dist,mx,my,mdown
    glfw.init()
    win=glfw.create_window(1100,680,"Simulasi Perlintasan Kereta Api 3D - OpenGL",None,None)
    glfw.make_context_current(win)

    # Callback resize window
    def on_resize(w, width, height):
        if height == 0: height = 1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width/height, 0.1, 300.0)
        glMatrixMode(GL_MODELVIEW)

    glfw.set_framebuffer_size_callback(win, on_resize)

    def on_key(w,key,sc,act,mod):
        global dist
        if act in(glfw.PRESS,glfw.REPEAT):
            if key==glfw.KEY_ESCAPE: glfw.set_window_should_close(w,True)
            if key==glfw.KEY_EQUAL:  dist=max(5.0,dist-1.5)
            if key==glfw.KEY_MINUS:  dist=min(50.0,dist+1.5)
    def on_mouse(w,btn,act,mod):
        global mdown,mx,my
        if btn==glfw.MOUSE_BUTTON_LEFT:
            mdown=(act==glfw.PRESS)
            if mdown: mx,my=glfw.get_cursor_pos(w)
    def on_move(w,x,y):
        global yaw,pitch,mx,my
        if mdown:
            yaw+=(x-mx)*0.4
            pitch=max(5.0,min(85.0,pitch+(y-my)*0.3))
            mx,my=x,y
    def on_scroll(w,dx,dy):
        global dist
        dist=max(5.0,min(50.0,dist-dy))

    glfw.set_key_callback(win,on_key)
    glfw.set_mouse_button_callback(win,on_mouse)
    glfw.set_cursor_pos_callback(win,on_move)
    glfw.set_scroll_callback(win,on_scroll)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK,GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH); glEnable(GL_NORMALIZE)
    glLightfv(GL_LIGHT0,GL_AMBIENT,[0.4,0.4,0.38,1.0])
    glLightfv(GL_LIGHT0,GL_DIFFUSE,[0.9,0.88,0.8,1.0])
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45,1100/680,0.1,300.0)
    glMatrixMode(GL_MODELVIEW)

    print("Simulasi Perlintasan Kereta Api 3D")
    print("DRAG=putar | SCROLL=zoom | ESC=keluar")
    prev=time.time()

    while not glfw.window_should_close(win):
        now=time.time(); dt=min(now-prev,0.05); prev=now
        glfw.poll_events(); update(dt)
        pr=math.radians(pitch); yr=math.radians(yaw)
        cx=dist*math.cos(pr)*math.sin(yr)
        cy=dist*math.sin(pr)
        cz=dist*math.cos(pr)*math.cos(yr)
        glClearColor(0.52,0.78,0.92,1.0)
        w, h = glfw.get_framebuffer_size(win)
        glViewport(0, 0, w, h)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glLightfv(GL_LIGHT0,GL_POSITION,[10,20,10,1])
        gluLookAt(cx,cy,cz, 0,0.5,0, 0,1,0)
        draw_jalan(); draw_rel()
        draw_portal(palang,merah)
        for k in kendaraan: k.draw()
        if fase in(1,2,3): draw_kereta(kereta_x)
        glfw.swap_buffers(win)

    glfw.terminate()

main()