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
    glRotatef(-90,1,0,0)
    q=gluNewQuadric()
    glColor3f(0.35,0.20,0.08); gluCylinder(q,0.18,0.12,1.8,7,1)
    glColor3f(0.18,0.50,0.15); glTranslatef(0,0,1.5); gluCylinder(q,1.1,0.0,1.4,9,1)
    glTranslatef(0,0,0.8); gluCylinder(q,0.9,0.0,1.2,9,1)
    glTranslatef(0,0,0.7); gluCylinder(q,0.65,0.0,1.0,9,1)
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
def draw_tiang_vertikal(x,y,z,r,h,sl,cr,cg,cb):
    glPushMatrix(); glTranslatef(x,y,z)
    glRotatef(-90,1,0,0)
    q=gluNewQuadric(); gluCylinder(q,r,r,h,sl,1)
    gluDisk(q,0,r,sl,1); glTranslatef(0,0,h); gluDisk(q,0,r,sl,1)
    gluDeleteQuadric(q); glPopMatrix()

def draw_satu_palang(x,z,sudut,arah=1):
    glPushMatrix(); glTranslatef(x,0,z)
    box(0,0.1,0,0.5,0.2,0.5,0.3,0.3,0.3)
    draw_tiang_vertikal(0,0.2,0,0.12,1.4,10,0.15,0.15,0.15)
    box(0,1.65,0,0.42,0.32,0.42,0.12,0.12,0.12)
    bola(0,1.90,0,0.11,cr=0.9,cg=0.1,cb=0.1)
    # arah=-1 (palang ke kiri) perlu sudut negatif agar naik ke atas, bukan ke bawah
    sudut_efektif = sudut if arah==1 else -sudut
    glTranslatef(0,1.65,0); glRotatef(sudut_efektif,0,0,1)
    for i in range(14):   # diperpanjang: 14 segmen
        px=arah*(i*0.5+0.25)
        if i%2==0: box(px,0,0,0.48,0.13,0.13,0.9,0.1,0.1)
        else:      box(px,0,0,0.48,0.13,0.13,0.95,0.95,0.95)
    bola(arah*7.25,0,0,0.18,cr=0.9,cg=0.1,cb=0.1)
    box(arah*3.5,0.08,0,6.8,0.04,0.14,1.0,0.85,0.0)
    glPopMatrix()

def draw_lampu(x,z,merah,arah_z=1):
    box(x,0.1,z,0.55,0.2,0.55,0.28,0.28,0.28)
    draw_tiang_vertikal(x,0.2,z,0.10,2.2,10,0.18,0.18,0.18)
    draw_tiang_vertikal(x,2.4,z,0.085,1.0,10,0.18,0.18,0.18)
    # Housing membelakangi: lampu z- → housing ke z- (arah_z=-1), lampu z+ → ke z+ (arah_z=+1)
    lz = z + arah_z*1.0
    box(x,3.55,z+arah_z*0.5,0.1,0.1,1.1,0.18,0.18,0.18)
    box(x,3.55,lz,0.28,0.75,0.22,0.08,0.08,0.08)
    box(x,3.95,lz,0.32,0.08,0.28,0.12,0.12,0.12)
    if merah: bola(x,3.72,lz,0.14,cr=1.0,cg=0.05,cb=0.05)
    else:     bola(x,3.72,lz,0.14,cr=0.25,cg=0.0,cb=0.0)
    if not merah: bola(x,3.35,lz,0.14,cr=0.05,cg=1.0,cb=0.05)
    else:         bola(x,3.35,lz,0.14,cr=0.0,cg=0.18,cb=0.0)

def draw_prisma_atap(cx,cy,cz,lx,tinggi,lz,r,g,b):
    glColor3f(r,g,b)
    hx=lx/2; hz=lz/2
    glBegin(GL_TRIANGLES)
    glNormal3f(-tinggi,hx,0)
    glVertex3f(cx-hx,cy,cz-hz); glVertex3f(cx,cy+tinggi,cz-hz); glVertex3f(cx,cy+tinggi,cz+hz)
    glVertex3f(cx-hx,cy,cz-hz); glVertex3f(cx,cy+tinggi,cz+hz); glVertex3f(cx-hx,cy,cz+hz)
    glNormal3f(tinggi,hx,0)
    glVertex3f(cx+hx,cy,cz-hz); glVertex3f(cx,cy+tinggi,cz+hz); glVertex3f(cx,cy+tinggi,cz-hz)
    glVertex3f(cx+hx,cy,cz-hz); glVertex3f(cx+hx,cy,cz+hz);    glVertex3f(cx,cy+tinggi,cz+hz)
    glNormal3f(0,0,-1)
    glVertex3f(cx-hx,cy,cz-hz); glVertex3f(cx+hx,cy,cz-hz); glVertex3f(cx,cy+tinggi,cz-hz)
    glNormal3f(0,0,1)
    glVertex3f(cx-hx,cy,cz+hz); glVertex3f(cx,cy+tinggi,cz+hz); glVertex3f(cx+hx,cy,cz+hz)
    glEnd()

def draw_pos_jaga():
    px, pz = 9.5, 9.0
    tw=0.18; w=1.4; h=1.7
    wc=(0.82,0.78,0.70)
    xl = px - w - tw/2
    xr = px + w + tw/2
    zf = pz - w - tw/2
    zb = pz + w + tw/2

    # Pondasi
    box(px,0.08,pz,(w+tw)*2,0.16,(w+tw)*2,0.35,0.32,0.28)

    # Tembok 4 sisi full
    box(px,    h/2+0.16, zf, (w+tw)*2, h, tw, *wc)
    box(px,    h/2+0.16, zb, (w+tw)*2, h, tw, *wc)
    box(xl,    h/2+0.16, pz, tw, h, w*2, *wc)
    box(xr,    h/2+0.16, pz, tw, h, w*2, *wc)

    # Jendela depan (2 buah, menonjol keluar 0.15)
    jof = 0.15
    for jx in [px-0.55, px+0.40]:
        box(jx,    1.05, zf-jof,       0.72, 0.52, 0.06, 0.55, 0.80, 0.92)
        box(jx,    1.05, zf-jof-0.03,  0.82, 0.62, 0.06, 0.38, 0.22, 0.08)
        box(jx,    1.05, zf-jof-0.01,  0.72, 0.04, 0.07, 0.30, 0.18, 0.06)
        box(jx,    1.05, zf-jof-0.01,  0.04, 0.52, 0.07, 0.30, 0.18, 0.06)

    # Pintu kiri (menonjol keluar 0.15)
    pof = 0.15
    box(xl-pof,      0.55, pz,      0.06, 1.00, 0.82, 0.42, 0.26, 0.12)
    box(xl-pof-0.04, 0.55, pz,      0.05, 1.08, 0.94, 0.28, 0.16, 0.06)
    box(xl-pof-0.02, 1.12, pz,      0.08, 0.07, 0.88, 0.25, 0.14, 0.05)
    box(xl-pof-0.06, 0.60, pz-0.18, 0.08, 0.08, 0.08, 0.72, 0.60, 0.40)

    # Jendela samping kanan (menonjol keluar 0.15)
    box(xr+pof,      1.05, pz,      0.06, 0.52, 0.74, 0.55, 0.80, 0.92)
    box(xr+pof+0.03, 1.05, pz,      0.05, 0.62, 0.84, 0.38, 0.22, 0.08)
    box(xr+pof+0.01, 1.05, pz,      0.07, 0.04, 0.74, 0.30, 0.18, 0.06)
    box(xr+pof+0.01, 1.05, pz,      0.07, 0.52, 0.04, 0.30, 0.18, 0.06)

    # Atap prisma
    atap_lx = (w+tw)*2+0.25
    atap_lz = (w+tw)*2+0.25
    atap_y  = h+0.22
    box(px, h+0.16, pz, atap_lx+0.05, 0.12, atap_lz+0.05, 0.55,0.22,0.10)
    draw_prisma_atap(px, atap_y, pz, atap_lx, 0.85, atap_lz, 0.62,0.18,0.08)
    # Bubungan = ridge di puncak prisma, sepanjang sisi z atap
    box(px, atap_y+0.85, pz, 0.18, 0.10, atap_lz+0.10, 0.45,0.14,0.06)

    # Pagar mengelilingi bangunan (jarak 1.5 dari tembok)
    gap = 1.5
    fx0 = xl - gap;   fx1 = xr + gap
    fz0 = zf - gap;   fz1 = zb + gap
    pc = (0.55, 0.38, 0.22)
    tr = 0.05; th = 0.65
    for fx in [fx0, (fx0+fx1)/2-0.6, (fx0+fx1)/2+0.6, fx1]:
        draw_tiang_vertikal(fx, 0.16, fz0, tr, th, 6, *pc)
    for fx in [fx0, (fx0+fx1)/2, fx1]:
        draw_tiang_vertikal(fx, 0.16, fz1, tr, th, 6, *pc)
    for fz in [fz0+0.7, pz, fz1-0.7]:
        draw_tiang_vertikal(fx0, 0.16, fz, tr, th, 6, *pc)
    for fz in [fz0+0.7, pz, fz1-0.7]:
        draw_tiang_vertikal(fx1, 0.16, fz, tr, th, 6, *pc)
    lx = fx1-fx0; lz = fz1-fz0
    for fy in [0.38, 0.72]:
        box((fx0+fx1)/2, fy, fz0, lx, 0.06, 0.06, *pc)
        box((fx0+fx1)/2, fy, fz1, lx, 0.06, 0.06, *pc)
        box(fx0, fy, (fz0+fz1)/2, 0.06, 0.06, lz, *pc)
        box(fx1, fy, (fz0+fz1)/2, 0.06, 0.06, lz, *pc)
    # Pintu pagar di sisi kiri (fx0), sejajar z dengan pintu pos (pz)
    box(fx0-0.03, 0.45, pz, 0.05, 0.60, 0.55, 0.45,0.30,0.14)

def draw_portal(sudut,merah):
    # 2 palang: sisi kiri (x=-4.5) menjulur ke kanan, sisi kanan (x=+4.5) ke kiri
    draw_satu_palang(-4.5, -2.5, sudut, arah=+1)
    draw_satu_palang( 4.5,  2.5, sudut, arah=-1)
    # Lampu sisi kanan (x=+4.5), jauh dari pos, housing ke z-
    draw_lampu( 4.5, -3.5, merah, arah_z=-1)
    # Lampu sisi kiri/seberang (x=-4.5), dekat pos dipindah ke seberang, housing ke z+
    draw_lampu(-4.5,  3.5, merah, arah_z=+1)
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
    glPushMatrix()
    glTranslatef(px, 0, 0)
    glRotatef(180, 0, 1, 0)
    draw_lokomotif(0)
    glPopMatrix()
    for i in range(4):
        draw_gerbong(px + 5.8 + i * 5.6)

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
        self.arah=1 if x<0 else -1
        self.speed=4.0
    def update(self,dt,tutup,depan_z=None):
        jarak_aman = 4.5 if self.tipe=='mobil' else 3.5
        if tutup:
            batas = 4.0 * self.arah
            dekat_palang = (self.arah==1 and self.z >= batas) or \
                           (self.arah==-1 and self.z <= batas)
            if dekat_palang: return
        if depan_z is not None:
            jarak = (depan_z - self.z) * self.arah
            if jarak < jarak_aman: return
        self.z += self.arah * self.speed * dt
        if self.z >  32: self.z = -32
        if self.z < -32: self.z =  32
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        if self.arah == -1: glRotatef(180, 0, 1, 0)
        if self.tipe=='mobil': draw_mobil(0, 0, self.warna)
        else:                  draw_motor(0, 0, self.warna)
        glPopMatrix()

def buat_kendaraan():
    kd=[]
    for i,t,w in [(-22,'mobil',0),(-13,'motor',2),(-4,'mobil',4),(5,'mobil',1),(14,'motor',3),(23,'mobil',6)]:
        kd.append(Kendaraan(i,-1.5,t,w))
    for i,t,w in [(22,'mobil',5),(13,'motor',1),(4,'mobil',2),(-5,'motor',0),(-14,'mobil',3),(-23,'mobil',6)]:
        kd.append(Kendaraan(i,1.5,t,w))
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
        if kereta_x < -30.0: fase=3; ftimer=0.0
    elif fase==3:
        merah=True; palang=lerp(0.0,90.0,ftimer/2.0)
        kereta_x-=14.0*dt
        if ftimer>2.0: fase=0; ftimer=0.0; merah=False; palang=90.0; kereta_x=55.0
    tutup = fase in(1,2,3)
    jalur_kiri  = sorted([k for k in kendaraan if k.x < 0], key=lambda k: k.z)
    jalur_kanan = sorted([k for k in kendaraan if k.x > 0], key=lambda k: -k.z)
    for jalur in (jalur_kiri, jalur_kanan):
        for i, k in enumerate(jalur):
            depan = jalur[i-1] if i > 0 else None
            k.update(dt, tutup, depan.z if depan else None)

def main():
    global yaw,pitch,dist,mx,my,mdown
    glfw.init()
    win=glfw.create_window(1100,680,"Simulasi Perlintasan Kereta Api 3D - OpenGL",None,None)
    glfw.make_context_current(win)

    def on_resize(w, width, height):
        if height == 0: height = 1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
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