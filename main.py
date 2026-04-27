"""
Simulasi Perlintasan Kereta Api 3D - OpenGL
============================================
Kontrol:
  DRAG kiri  = putar kamera (mode overview)
  SCROLL     = zoom
  1          = Mode Kamera 1 - Overview (default)
  2          = Mode Kamera 2 - Driver POV (dashcam dari dalam kendaraan)
  3          = Mode Kamera 3 - Trackside / samping rel
  TAB / N    = (mode driver) kendaraan berikutnya
  P          = (mode driver) kendaraan sebelumnya
  SPACE      = Pause / Resume
  F / S      = Speed Up / Slow Down
  ESC        = Keluar
"""

import glfw
import math
import time
from OpenGL.GL import *
from OpenGL.GLU import *

# ═══════════════════════════════════════════════
#  KONSTANTA STATE
# ═══════════════════════════════════════════════
FASE_IDLE      = 0   # Palang terbuka, kereta menunggu
FASE_TUTUP     = 1   # Palang sedang menutup, lampu merah
FASE_KERETA    = 2   # Kereta melintas
FASE_BUKA      = 3   # Palang sedang membuka

# Mode kamera
CAM_OVERVIEW   = 1
CAM_DRIVER     = 2
CAM_TRACKSIDE  = 3

# ═══════════════════════════════════════════════
#  HELPER GEOMETRI
# ═══════════════════════════════════════════════
def box(cx, cy, cz, sx, sy, sz, r, g, b):
    glColor3f(r, g, b)
    hx, hy, hz = sx/2, sy/2, sz/2
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0);  glVertex3f(-hx,hy,-hz); glVertex3f(hx,hy,-hz); glVertex3f(hx,hy,hz);  glVertex3f(-hx,hy,hz)
    glNormal3f(0,-1, 0);  glVertex3f(-hx,-hy,hz); glVertex3f(hx,-hy,hz); glVertex3f(hx,-hy,-hz); glVertex3f(-hx,-hy,-hz)
    glNormal3f(0, 0, 1);  glVertex3f(-hx,-hy,hz); glVertex3f(hx,-hy,hz); glVertex3f(hx,hy,hz);  glVertex3f(-hx,hy,hz)
    glNormal3f(0, 0,-1);  glVertex3f(-hx,hy,-hz); glVertex3f(hx,hy,-hz); glVertex3f(hx,-hy,-hz); glVertex3f(-hx,-hy,-hz)
    glNormal3f(-1,0, 0);  glVertex3f(-hx,-hy,-hz); glVertex3f(-hx,-hy,hz); glVertex3f(-hx,hy,hz); glVertex3f(-hx,hy,-hz)
    glNormal3f(1, 0, 0);  glVertex3f(hx,-hy,hz);  glVertex3f(hx,-hy,-hz); glVertex3f(hx,hy,-hz); glVertex3f(hx,hy,hz)
    glEnd()
    glPopMatrix()

def silinder(cx, cy, cz, r, h, sl=10, cr=0.5, cg=0.5, cb=0.5):
    glColor3f(cr, cg, cb)
    glPushMatrix(); glTranslatef(cx, cy, cz)
    q = gluNewQuadric(); gluCylinder(q, r, r, h, sl, 1)
    gluDisk(q, 0, r, sl, 1); glTranslatef(0, 0, h); gluDisk(q, 0, r, sl, 1)
    gluDeleteQuadric(q); glPopMatrix()

def bola(cx, cy, cz, r, sl=10, st=10, cr=1, cg=1, cb=1):
    glColor3f(cr, cg, cb)
    glPushMatrix(); glTranslatef(cx, cy, cz)
    q = gluNewQuadric(); gluSphere(q, r, sl, st)
    gluDeleteQuadric(q); glPopMatrix()

def tiang_vertikal(x, y, z, r, h, sl, cr, cg, cb):
    glPushMatrix(); glTranslatef(x, y, z); glRotatef(-90, 1, 0, 0)
    q = gluNewQuadric(); gluCylinder(q, r, r, h, sl, 1)
    gluDisk(q, 0, r, sl, 1); glTranslatef(0, 0, h); gluDisk(q, 0, r, sl, 1)
    gluDeleteQuadric(q); glPopMatrix()

def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))

# ═══════════════════════════════════════════════
#  LINGKUNGAN
# ═══════════════════════════════════════════════
def draw_pohon(x, z):
    glPushMatrix(); glTranslatef(x, 0, z); glRotatef(-90, 1, 0, 0)
    q = gluNewQuadric()
    glColor3f(0.35, 0.20, 0.08); gluCylinder(q, 0.18, 0.12, 1.8, 7, 1)
    glColor3f(0.18, 0.50, 0.15); glTranslatef(0, 0, 1.5); gluCylinder(q, 1.1, 0.0, 1.4, 9, 1)
    glTranslatef(0, 0, 0.8);     gluCylinder(q, 0.9, 0.0, 1.2, 9, 1)
    glTranslatef(0, 0, 0.7);     gluCylinder(q, 0.65,0.0, 1.0, 9, 1)
    gluDeleteQuadric(q); glPopMatrix()

def draw_jalan():
    box(0,-0.05, 0, 100,0.10,60,  0.25,0.45,0.18)
    box(0, 0.02, 0, 100,0.04,3.5, 0.48,0.46,0.44)
    box(0, 0.03, 0, 8.0,0.06,60,  0.20,0.20,0.22)
    for i in range(-14,15):
        zi = i * 2.0
        if abs(zi) < 2.5: continue
        box(0, 0.07, zi, 0.15,0.01,1.0, 0.9,0.9,0.9)
    box(0, 0.03,-4.5, 8.0,0.05,1.0, 0.16,0.16,0.18)
    box(0, 0.03, 4.5, 8.0,0.05,1.0, 0.16,0.16,0.18)
    for zi in [-22,-16,-11,-7, 7,11,16,22]:
        draw_pohon(-6.0, zi); draw_pohon(6.0, zi)


def draw_jalan_cabang():
    """
    Jalan cabang horizontal (sumbu X) di sisi utara (z=-28) dan selatan (z=+28).
    Memberi kesan ada persimpangan / interchange di ujung jalan utama.
    """
    aspal = (0.20, 0.20, 0.22)
    bahu  = (0.48, 0.46, 0.44)
    marka = (0.9,  0.9,  0.9 )

    for zc in (-28.0, 28.0):
        # Badan jalan cabang (sumbu X, lebar 6, panjang 60)
        box(0, 0.03, zc, 60, 0.06, 6.0, *aspal)
        # Bahu jalan / shoulder
        box(0, 0.025, zc-3.2, 60, 0.04, 0.6, *bahu)
        box(0, 0.025, zc+3.2, 60, 0.04, 0.6, *bahu)
        # Marka tengah putus-putus
        for xi in range(-14, 15):
            xi2 = xi * 2.2
            box(xi2, 0.07, zc, 0.15, 0.01, 1.0, *marka)
        # Marka tepi solid
        box(0, 0.065, zc-2.6, 60, 0.01, 0.12, *marka)
        box(0, 0.065, zc+2.6, 60, 0.01, 0.12, *marka)

        # Trotoar sisi jalan cabang
        trot = (0.68, 0.66, 0.63)
        box(0, 0.11, zc-4.0, 60, 0.22, 2.0, *trot)
        box(0, 0.11, zc+4.0, 60, 0.22, 2.0, *trot)

        # Pohon di pinggir jalan cabang (tiap 4 unit)
        for xi in range(-13, 14, 4):
            if abs(xi) < 5: continue   # jangan tumbuh di persimpangan
            draw_pohon(xi, zc - 5.5)
            draw_pohon(xi, zc + 5.5)

    # ── Jalan penghubung / on-ramp kiri (x=-20, menyambung jalan utama ke cabang) ──
    for xc in (-20.0, 20.0):
        # Ramp vertikal (sumbu Z) menghubungkan jalan utama ke jalan cabang
        box(xc, 0.03, 0, 4.0, 0.06, 56, *aspal)
        # Marka tepi ramp
        box(xc-1.8, 0.065, 0, 0.12, 0.01, 56, *marka)
        box(xc+1.8, 0.065, 0, 0.12, 0.01, 56, *marka)
        # Marka tengah putus-putus ramp
        for zi in range(-13, 14):
            zi2 = zi * 2.0
            if abs(zi2) < 3: continue
            box(xc, 0.07, zi2, 0.12, 0.01, 1.0, *marka)
        # Trotoar ramp
        box(xc-2.8, 0.11, 0, 1.2, 0.22, 56, *trot)
        box(xc+2.8, 0.11, 0, 1.2, 0.22, 56, *trot)
        # Pohon di ramp
        for zi in range(-12, 13, 5):
            if abs(zi) < 4: continue
            draw_pohon(xc - 4.0, zi)
            draw_pohon(xc + 4.0, zi)

def draw_rel():
    for i in range(-27,28):
        box(i*1.5, 0.05, 0, 1.2,0.12,1.8, 0.40,0.25,0.10)
    box(0,0.18,-0.7, 80,0.10,0.15, 0.6,0.6,0.65)
    box(0,0.24,-0.7, 80,0.05,0.22, 0.7,0.7,0.75)
    box(0,0.18, 0.7, 80,0.10,0.15, 0.6,0.6,0.65)
    box(0,0.24, 0.7, 80,0.05,0.22, 0.7,0.7,0.75)

# ═══════════════════════════════════════════════
#  PORTAL & PALANG
# ═══════════════════════════════════════════════
def draw_satu_palang(x, z, sudut, arah=1):
    glPushMatrix(); glTranslatef(x, 0, z)
    box(0, 0.1, 0, 0.5,0.2,0.5, 0.3,0.3,0.3)
    tiang_vertikal(0, 0.2, 0, 0.12, 0.8, 10, 0.15,0.15,0.15)
    box(0, 1.05, 0, 0.42,0.32,0.42, 0.12,0.12,0.12)
    bola(0, 1.30, 0, 0.11, cr=0.9, cg=0.1, cb=0.1)
    sudut_efektif = sudut if arah == 1 else -sudut
    glTranslatef(0, 1.05, 0); glRotatef(sudut_efektif, 0, 0, 1)
    for i in range(14):
        px = arah * (i*0.5 + 0.25)
        if i % 2 == 0: box(px, 0, 0, 0.48,0.13,0.13, 0.9,0.1,0.1)
        else:          box(px, 0, 0, 0.48,0.13,0.13, 0.95,0.95,0.95)
    bola(arah*7.25, 0, 0, 0.18, cr=0.9, cg=0.1, cb=0.1)
    box(arah*3.5, 0.08, 0, 6.8,0.04,0.14, 1.0,0.85,0.0)
    glPopMatrix()

def draw_lampu(x, z, merah, arah_z=1):
    box(x, 0.1, z, 0.55,0.2,0.55, 0.28,0.28,0.28)
    tiang_vertikal(x, 0.2, z, 0.10, 2.2, 10, 0.18,0.18,0.18)
    tiang_vertikal(x, 2.4, z, 0.085,1.0, 10, 0.18,0.18,0.18)
    lz = z + arah_z * 1.0
    box(x, 3.55, z+arah_z*0.5, 0.1,0.1,1.1, 0.18,0.18,0.18)
    box(x, 3.55, lz, 0.28,0.75,0.22, 0.08,0.08,0.08)
    box(x, 3.95, lz, 0.32,0.08,0.28, 0.12,0.12,0.12)
    if merah: bola(x, 3.72, lz, 0.14, cr=1.0,cg=0.05,cb=0.05)
    else:     bola(x, 3.72, lz, 0.14, cr=0.25,cg=0.0,cb=0.0)
    if not merah: bola(x, 3.35, lz, 0.14, cr=0.05,cg=1.0,cb=0.05)
    else:         bola(x, 3.35, lz, 0.14, cr=0.0,cg=0.18,cb=0.0)

def draw_prisma_atap(cx,cy,cz,lx,tinggi,lz,r,g,b):
    glColor3f(r,g,b)
    hx=lx/2; hz=lz/2
    glBegin(GL_TRIANGLES)
    glNormal3f(-tinggi,hx,0)
    glVertex3f(cx-hx,cy,cz-hz); glVertex3f(cx,cy+tinggi,cz-hz); glVertex3f(cx,cy+tinggi,cz+hz)
    glVertex3f(cx-hx,cy,cz-hz); glVertex3f(cx,cy+tinggi,cz+hz); glVertex3f(cx-hx,cy,cz+hz)
    glNormal3f(tinggi,hx,0)
    glVertex3f(cx+hx,cy,cz-hz); glVertex3f(cx,cy+tinggi,cz+hz); glVertex3f(cx,cy+tinggi,cz-hz)
    glVertex3f(cx+hx,cy,cz-hz); glVertex3f(cx+hx,cy,cz+hz);   glVertex3f(cx,cy+tinggi,cz+hz)
    glNormal3f(0,0,-1)
    glVertex3f(cx-hx,cy,cz-hz); glVertex3f(cx+hx,cy,cz-hz); glVertex3f(cx,cy+tinggi,cz-hz)
    glNormal3f(0,0,1)
    glVertex3f(cx-hx,cy,cz+hz); glVertex3f(cx,cy+tinggi,cz+hz); glVertex3f(cx+hx,cy,cz+hz)
    glEnd()

def draw_pos_jaga():
    px,pz = 9.5, 9.0
    tw=0.18; w=1.4; h=1.7
    wc=(0.82,0.78,0.70)
    xl = px-w-tw/2; xr = px+w+tw/2
    zf = pz-w-tw/2; zb = pz+w+tw/2
    box(px,0.08,pz,(w+tw)*2,0.16,(w+tw)*2,0.35,0.32,0.28)
    box(px,h/2+0.16,zf,(w+tw)*2,h,tw,*wc)
    box(px,h/2+0.16,zb,(w+tw)*2,h,tw,*wc)
    box(xl,h/2+0.16,pz,tw,h,w*2,*wc)
    box(xr,h/2+0.16,pz,tw,h,w*2,*wc)
    jof=0.15
    for jx in [px-0.55,px+0.40]:
        box(jx,1.05,zf-jof,0.72,0.52,0.06,0.55,0.80,0.92)
        box(jx,1.05,zf-jof-0.03,0.82,0.62,0.06,0.38,0.22,0.08)
        box(jx,1.05,zf-jof-0.01,0.72,0.04,0.07,0.30,0.18,0.06)
        box(jx,1.05,zf-jof-0.01,0.04,0.52,0.07,0.30,0.18,0.06)
    pof=0.15
    box(xl-pof,0.55,pz,0.06,1.00,0.82,0.42,0.26,0.12)
    box(xl-pof-0.04,0.55,pz,0.05,1.08,0.94,0.28,0.16,0.06)
    box(xl-pof-0.02,1.12,pz,0.08,0.07,0.88,0.25,0.14,0.05)
    box(xl-pof-0.06,0.60,pz-0.18,0.08,0.08,0.08,0.72,0.60,0.40)
    box(xr+pof,1.05,pz,0.06,0.52,0.74,0.55,0.80,0.92)
    box(xr+pof+0.03,1.05,pz,0.05,0.62,0.84,0.38,0.22,0.08)
    box(xr+pof+0.01,1.05,pz,0.07,0.04,0.74,0.30,0.18,0.06)
    box(xr+pof+0.01,1.05,pz,0.07,0.52,0.04,0.30,0.18,0.06)
    atap_lx=(w+tw)*2+0.25; atap_lz=(w+tw)*2+0.25; atap_y=h+0.22
    box(px,h+0.16,pz,atap_lx+0.05,0.12,atap_lz+0.05,0.55,0.22,0.10)
    draw_prisma_atap(px,atap_y,pz,atap_lx,0.85,atap_lz,0.62,0.18,0.08)
    box(px,atap_y+0.85,pz,0.18,0.10,atap_lz+0.10,0.45,0.14,0.06)
    gap=1.5; fx0=xl-gap; fx1=xr+gap; fz0=zf-gap; fz1=zb+gap
    pc=(0.55,0.38,0.22); tr=0.05; th=0.65
    for fx in [fx0,(fx0+fx1)/2-0.6,(fx0+fx1)/2+0.6,fx1]:
        tiang_vertikal(fx,0.16,fz0,tr,th,6,*pc)
    for fx in [fx0,(fx0+fx1)/2,fx1]:
        tiang_vertikal(fx,0.16,fz1,tr,th,6,*pc)
    for fz in [fz0+0.7,pz,fz1-0.7]:
        tiang_vertikal(fx0,0.16,fz,tr,th,6,*pc)
    for fz in [fz0+0.7,pz,fz1-0.7]:
        tiang_vertikal(fx1,0.16,fz,tr,th,6,*pc)
    lx=fx1-fx0; lz=fz1-fz0
    for fy in [0.38,0.72]:
        box((fx0+fx1)/2,fy,fz0,lx,0.06,0.06,*pc)
        box((fx0+fx1)/2,fy,fz1,lx,0.06,0.06,*pc)
        box(fx0,fy,(fz0+fz1)/2,0.06,0.06,lz,*pc)
        box(fx1,fy,(fz0+fz1)/2,0.06,0.06,lz,*pc)
    box(fx0-0.03,0.45,pz,0.05,0.60,0.55,0.45,0.30,0.14)

def draw_rumah_indo(x, z, rot, warna_tembok):
    """Rumah khas Indonesia dengan atap genteng prisma."""
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(rot, 0, 1, 0)
    # Tembok Utama
    box(0, 1.0, 0, 3.5, 2.0, 3.5, *warna_tembok)
    # Pintu (Coklat)
    box(0, 0.7, 1.76, 0.7, 1.4, 0.05, 0.4, 0.2, 0.1)
    # Jendela
    box(1.0, 1.0, 1.76, 0.6, 0.6, 0.05, 0.8, 0.9, 1.0)
    # Atap Genteng (Oranye/Coklat)
    draw_prisma_atap(0, 2.0, 0, 4.2, 1.2, 4.2, 0.6, 0.2, 0.1)
    glPopMatrix()

def draw_indomaret(x, z, rot):
    """Gedung retail biru-merah-kuning khas Indonesia."""
    glPushMatrix()
    glTranslatef(x, 0, z)
    glRotatef(rot, 0, 1, 0)
    # Bangunan Utama (Putih)
    box(0, 1.5, 0, 6.0, 3.0, 4.0, 0.95, 0.95, 0.95)
    # List Warna Indomaret di atas (Biru, Merah, Kuning)
    box(0, 2.8, 2.02, 6.0, 0.4, 0.05, 0.0, 0.3, 0.7) # Biru
    box(-2.0, 2.8, 2.03, 1.0, 0.3, 0.05, 0.9, 0.1, 0.1) # Merah
    # Pintu Kaca Besar
    box(0, 1.0, 2.01, 2.5, 2.0, 0.05, 0.7, 0.85, 0.95)
    # Papan Iklan depan (Neon box)
    tiang_vertikal(2.5, 0, 3.0, 0.1, 4.0, 6, 0.3, 0.3, 0.3)
    box(2.5, 4.0, 3.0, 1.5, 0.8, 0.2, 0.0, 0.3, 0.7) # Background biru neon box
    glPopMatrix()

def draw_bangunan():
    """Tempatkan rumah dan ruko di semua sisi perlintasan."""
    # ── Sisi kiri jalan (x negatif) ──────────────────────────
    # Rumah-rumah di sepanjang jalur kiri
    draw_rumah_indo(-10, -18, 90,  (0.90, 0.85, 0.75))
    draw_rumah_indo(-10, -10, 90,  (0.80, 0.70, 0.60))
    draw_rumah_indo(-10,  -6, 90,  (0.75, 0.80, 0.70))
    draw_rumah_indo(-10,   8, 90,  (0.88, 0.78, 0.65))
    draw_rumah_indo(-10,  16, 90,  (0.70, 0.75, 0.80))
    draw_rumah_indo(-10,  24, 90,  (0.85, 0.72, 0.68))

    # Ruko di sisi kiri dekat perlintasan
    draw_indomaret(-14,   5, 90)
    draw_indomaret(-14, -12, 90)

    # ── Sisi kanan jalan (x positif) ─────────────────────────
    draw_rumah_indo(10, -20, -90, (0.82, 0.76, 0.65))
    draw_rumah_indo(10,  -8, -90, (0.78, 0.82, 0.72))
    draw_rumah_indo(10,   6, -90, (0.88, 0.80, 0.68))
    draw_rumah_indo(10,  12, -90, (0.72, 0.78, 0.85))
    draw_rumah_indo(10,  22, -90, (0.80, 0.70, 0.72))

    # Ruko di sisi kanan
    draw_indomaret(14,  10, -90)
    draw_indomaret(14, -15, -90)

    # ── Belakang rel (z negatif, sisi jauh) ──────────────────
    draw_rumah_indo(-18, -25, 0,  (0.85, 0.80, 0.70))
    draw_rumah_indo( -8, -25, 0,  (0.75, 0.82, 0.68))
    draw_rumah_indo(  8, -25, 0,  (0.90, 0.75, 0.65))
    draw_rumah_indo( 12, -25, 0,  (0.80, 0.85, 0.72))
    draw_indomaret(  20, -25, 0)

    # ── Depan rel (z positif, sisi dekat kamera default) ─────
    draw_rumah_indo(-18,  25, 180, (0.88, 0.78, 0.70))
    draw_rumah_indo( -8,  25, 180, (0.78, 0.80, 0.75))
    draw_rumah_indo(  8,  25, 180, (0.82, 0.72, 0.68))
    draw_rumah_indo( 12,  25, 180, (0.76, 0.82, 0.78))
    draw_indomaret( 20,  25, 180)

def draw_zebra_dan_trotoar():
    """Zebra crossing, stop line, dan trotoar di kanan-kiri jalan."""

    # ── Trotoar (sidewalk) kanan & kiri ──────────────────────────────────
    # Permukaan trotoar sedikit lebih tinggi dari jalan (y ≈ 0.12)
    trotoar_col = (0.68, 0.66, 0.63)
    kerb_col    = (0.50, 0.48, 0.46)
    for sx in (5.0, -5.0):
        box(sx, 0.11,  0, 2.0, 0.22, 56, *trotoar_col)   # permukaan
        # Kanstin / kerb pemisah jalan-trotoar
        box(sx * 0.82, 0.06, 0, 0.20, 0.12, 56, *kerb_col)
    # Ubin trotoar (garis melintang setiap 1.5 unit, warna kontras ringan)
    for sz in range(-27, 28, 2):
        box( 5.0, 0.225, sz, 2.0, 0.005, 0.05, 0.55, 0.53, 0.51)
        box(-5.0, 0.225, sz, 2.0, 0.005, 0.05, 0.55, 0.53, 0.51)

    # ── Garis berhenti (stop line) sebelum palang ────────────────────────
    # Jalur dari -z (arah+1): stop line di z ≈ -4.5
    box(0, 0.055, -4.5, 8.0, 0.02, 0.20, 0.92, 0.92, 0.92)
    # Jalur dari +z (arah-1): stop line di z ≈ +4.5
    box(0, 0.055,  4.5, 8.0, 0.02, 0.20, 0.92, 0.92, 0.92)

    # ── Zebra crossing ────────────────────────────────────────────────────
    lebar   = 0.50   # lebar satu garis (arah Z)
    celah   = 0.35   # celah antar garis
    n       = 6      # jumlah garis per zebra
    total_z = n * lebar + (n - 1) * celah   # ~4.25 unit
    # Letakkan zebra di z = ±7.0
    for zc in (7.0, -7.0):
        z0 = zc - total_z / 2
        for i in range(n):
            zs = z0 + i * (lebar + celah) + lebar / 2
            box(0, 0.055, zs, 7.4, 0.02, lebar, 0.93, 0.93, 0.93)


def draw_portal(sudut, merah):
    draw_satu_palang(-4.5,-2.5, sudut, arah=+1)
    draw_satu_palang( 4.5, 2.5, sudut, arah=-1)
    draw_lampu( 4.5,-3.5, merah, arah_z=-1)
    draw_lampu(-4.5, 3.5, merah, arah_z=+1)
    draw_pos_jaga()




# ═══════════════════════════════════════════════
#  KERETA
# ═══════════════════════════════════════════════
def draw_roda_kereta(cx, cy, cz):
    silinder(cx,cy,cz-0.7,0.08,1.4,8,0.3,0.3,0.3)
    for oz in [-0.7,0.7]:
        glPushMatrix(); glTranslatef(cx,cy,oz); glRotatef(90,1,0,0)
        glColor3f(0.15,0.15,0.15)
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
    draw_roda_kereta(-1.5,0.35,0); draw_roda_kereta(0.0,0.35,0); draw_roda_kereta(1.5,0.35,0)
    glPopMatrix()

def draw_gerbong(ox, r=0.15, g=0.45, b=0.70):
    glPushMatrix(); glTranslatef(ox,0,0)
    box(0,0.6,0,5.0,0.65,1.7,0.12,0.12,0.12)
    box(0,1.28,0,5.0,0.95,1.65,r,g,b)
    box(0,1.85,0,4.8,0.2,1.6,r*0.75,g*0.75,b*0.75)
    for jx in [-1.6,-0.4,0.8,2.0]:
        box(jx,1.35,0.84,0.9,0.38,0.03,0.8,0.9,0.95)
        box(jx,1.35,-0.84,0.9,0.38,0.03,0.8,0.9,0.95)
    draw_roda_kereta(-1.2,0.35,0); draw_roda_kereta(1.2,0.35,0)
    glPopMatrix()

def draw_kereta(px):
    glPushMatrix(); glTranslatef(px,0,0); glRotatef(180,0,1,0)
    draw_lokomotif(0); glPopMatrix()
    for i in range(4):
        draw_gerbong(px+5.8+i*5.6)

# ═══════════════════════════════════════════════
#  KENDARAAN
# ═══════════════════════════════════════════════
WARNA = [
    (0.8,0.12,0.12),(0.15,0.35,0.78),(0.88,0.75,0.10),
    (0.9,0.9,0.9),(0.12,0.12,0.12),(0.15,0.55,0.20),(0.8,0.45,0.10)
]

def draw_roda_k(x, y, z, r=0.28):
    tebal_ban = 0.15
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(90, 0, 1, 0) 
    glTranslatef(0, 0, -tebal_ban / 2)
    glColor3f(0.12, 0.12, 0.12)
    q = gluNewQuadric()
    # Gambar badan ban
    gluCylinder(q, r, r, tebal_ban, 15, 1)
    # Tutup roda sisi dalam
    gluDisk(q, 0, r, 15, 1)
    glTranslatef(0, 0, tebal_ban)
    gluDisk(q, 0, r, 15, 1)
    gluDeleteQuadric(q)
    glPopMatrix()

def draw_mobil(x, z, wi=0):
    r,g,b = WARNA[wi % len(WARNA)]
    glPushMatrix(); glTranslatef(x,0,z)
    box(0,0.32,0,1.0,0.52,2.2,r*0.85,g*0.85,b*0.85)
    box(0,0.82,0.1,0.9,0.45,1.35,r,g,b)
    box(0,0.85,0.82,0.85,0.35,0.04,0.6,0.82,0.92)
    box(0,0.85,-0.72,0.85,0.30,0.04,0.6,0.82,0.92)
    box( 0.38,0.38,1.11,0.18,0.12,0.04,1.0,1.0,0.8)
    box(-0.38,0.38,1.11,0.18,0.12,0.04,1.0,1.0,0.8)
    draw_roda_k(0.52,0.25,0.75); draw_roda_k(-0.52,0.25,0.75)
    draw_roda_k(0.52,0.25,-0.75); draw_roda_k(-0.52,0.25,-0.75)
    glPopMatrix()

def draw_motor_obj(x, z, wi=0):
    """Gambar objek motor - lebih detail dari sebelumnya."""
    r,g,b = WARNA[wi % len(WARNA)]
    glPushMatrix(); glTranslatef(x,0,z)
    # Badan utama motor
    box(0,0.42,0,  0.40,0.28,1.10, r,g,b)
    # Tangki bensin (membulat di atas)
    box(0,0.65,0.1,0.38,0.18,0.55, r*0.9,g*0.9,b*0.9)
    # Setang / handlebar
    box(0,0.78,0.48,0.68,0.07,0.07, 0.25,0.25,0.25)
    # Kepala / headlamp
    box(0,0.55,0.58,0.30,0.22,0.12, 0.15,0.15,0.15)
    bola(0,0.55,0.65,0.08, cr=1.0,cg=1.0,cb=0.7)
    # Knalpot
    box(0.22,0.28,-0.30,0.06,0.08,0.70, 0.50,0.50,0.50)
    # Mesin
    box(0,0.28,0,0.34,0.22,0.55, 0.20,0.20,0.22)
    # Kursi / seat
    box(0,0.62,-0.15,0.38,0.10,0.52, 0.12,0.10,0.10)
    # Roda depan & belakang (lebih tipis dari mobil)
    draw_roda_k( 0.10,0.22, 0.50,0.22)
    draw_roda_k(-0.10,0.22, 0.50,0.22)
    draw_roda_k( 0.10,0.22,-0.50,0.22)
    draw_roda_k(-0.10,0.22,-0.50,0.22)
    # Pengendara (silhouette sederhana)
    box(0,1.02,-0.10,0.30,0.40,0.28, 0.20,0.18,0.16)  # badan
    bola(0,1.32,-0.08,0.15, cr=0.85,cg=0.70,cb=0.55)   # kepala
    glPopMatrix()

# ─────────────────────────────────────────────
#  Kelas Kendaraan (state-driven)
# ─────────────────────────────────────────────
class Kendaraan:
    """
    Satu unit kendaraan (mobil / motor).
    State berhenti diatur oleh flag 'tutup' (palang tertutup)
    dan 'depan_z' (jarak aman dari kendaraan di depannya).
    """
    def __init__(self, z, x, tipe, warna):
        self.z     = float(z)
        self.x     = float(x)
        self.tipe  = tipe          # 'mobil' | 'motor'
        self.warna = warna
        self.arah  = 1 if x < 0 else -1   # x<0 → jalur kiri, bergerak ke +z
        self.speed = 3.8 if tipe == 'motor' else 3.2
        self.berhenti = False      # state eksplisit

    def update(self, dt, palang_tutup, depan_z=None, pejalan_list=None):
        """Update posisi kendaraan dengan logika berhenti."""
        jarak_aman   = 3.5 if self.tipe == 'motor' else 4.5
        panjang_body = 1.2 if self.tipe == 'motor' else 2.2

        # Cek apakah ada pejalan kaki yang benar-benar menghalangi lajur kendaraan ini.
        # Pejalan kaki bergerak dari x=-4.2 ke x=+4.5 melintasi badan jalan (x ≈ -4..+4).
        # Kendaraan jalur kiri x=-1.5, jalur kanan x=+1.5.
        # Hanya blocking jika:
        #   1. Pejalan kaki sudah masuk badan jalan (x > -3.5)
        #   2. Zebra crossing-nya ada di depan kendaraan (belum dilewati)
        ada_penyebrang = False
        if pejalan_list:
            for pk in pejalan_list:
                if not pk.aktif:
                    continue
                # Pejalan kaki hanya blocking jika sudah masuk badan jalan
                if pk.x < -3.5:
                    continue
                zc = pk.zc
                # Zebra harus ada di depan kendaraan (belum dilewati)
                if self.arah == 1:
                    zebra_di_depan = (self.z < zc + 2.5) and (self.z > zc - 14.0)
                else:
                    zebra_di_depan = (self.z > zc - 2.5) and (self.z < zc + 14.0)
                if zebra_di_depan:
                    ada_penyebrang = True
                    break

        # Berhenti jika palang tutup ATAU ada pejalan kaki menyebrang
        harus_berhenti = palang_tutup or ada_penyebrang

        STOP_LINE = 9.5
        batas_berhenti = -STOP_LINE * self.arah

        sudah_lewat = (
            (self.arah ==  1 and self.z >= batas_berhenti) or
            (self.arah == -1 and self.z <= batas_berhenti)
        )

        if harus_berhenti and not sudah_lewat:
            # Posisi berhenti terdepan: tepat sebelum zebra crossing
            default_stop = batas_berhenti - self.arah * panjang_body * 0.5

            if depan_z is not None:
                # Berhenti di belakang kendaraan di depan, dengan jarak aman
                posisi_berhenti = depan_z - self.arah * jarak_aman
                # Clamp: tidak boleh maju melewati stop line
                if self.arah == 1:
                    posisi_berhenti = min(posisi_berhenti, default_stop)
                else:
                    posisi_berhenti = max(posisi_berhenti, default_stop)
            else:
                posisi_berhenti = default_stop

            # Gerak perlahan menuju posisi berhenti
            selisih = (posisi_berhenti - self.z) * self.arah
            if selisih > 0.05:
                self.z += self.arah * self.speed * dt
                if (self.arah == 1  and self.z > posisi_berhenti) or \
                   (self.arah == -1 and self.z < posisi_berhenti):
                    self.z = posisi_berhenti
            self.berhenti = True
            return

        self.berhenti = False

        # Jaga jarak antar kendaraan saat berjalan
        if depan_z is not None:
            jarak = (depan_z - self.z) * self.arah
            if jarak < jarak_aman:
                return

        # Gerak maju
        self.z += self.arah * self.speed * dt

        # Wrap-around
        if self.z >  34: self.z = -34
        if self.z < -34: self.z =  34

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        if self.arah == -1:
            glRotatef(180, 0, 1, 0)
        if self.tipe == 'mobil':
            draw_mobil(0, 0, self.warna)
        else:
            draw_motor_obj(0, 0, self.warna)
        glPopMatrix()

    def world_pos(self):
        """Kembalikan posisi dunia (x, y, z) kendaraan."""
        return (self.x, 0.0, self.z)

    def heading_deg(self):
        """Arah hadap kendaraan dalam derajat (untuk kamera driver)."""
        return 0.0 if self.arah == 1 else 180.0


def draw_pejalan_kaki(x, z, phase, ukuran=1.0):
    """
    Gambar pejalan kaki sederhana (silhouette 3D).
    phase = 0..1 untuk animasi langkah kaki.
    """
    s = ukuran
    swing = math.sin(phase * math.pi * 2) * 0.18 * s

    glPushMatrix()
    glTranslatef(x, 0, z)

    # Badan
    box(0, 0.7*s, 0, 0.22*s, 0.40*s, 0.16*s, 0.25, 0.40, 0.70)
    # Kepala
    bola(0, 1.02*s, 0, 0.12*s, cr=0.88, cg=0.72, cb=0.55)

    # Kaki kiri
    glPushMatrix()
    glTranslatef(-0.06*s, 0.42*s, 0)
    glRotatef(swing * 80, 1, 0, 0)
    box(0, -0.18*s, 0, 0.10*s, 0.35*s, 0.10*s, 0.15, 0.15, 0.35)
    glPopMatrix()

    # Kaki kanan
    glPushMatrix()
    glTranslatef(0.06*s, 0.42*s, 0)
    glRotatef(-swing * 80, 1, 0, 0)
    box(0, -0.18*s, 0, 0.10*s, 0.35*s, 0.10*s, 0.15, 0.15, 0.35)
    glPopMatrix()

    # Tangan kiri
    glPushMatrix()
    glTranslatef(-0.16*s, 0.82*s, 0)
    glRotatef(-swing * 60, 1, 0, 0)
    box(0, -0.13*s, 0, 0.08*s, 0.26*s, 0.08*s, 0.25, 0.40, 0.70)
    glPopMatrix()

    # Tangan kanan
    glPushMatrix()
    glTranslatef(0.16*s, 0.82*s, 0)
    glRotatef(swing * 60, 1, 0, 0)
    box(0, -0.13*s, 0, 0.08*s, 0.26*s, 0.08*s, 0.25, 0.40, 0.70)
    glPopMatrix()

    glPopMatrix()


class PejalanKaki:
    """
    Pejalan kaki yang menyebrang saat lampu merah untuk kendaraan (zebra cross).
    Menyebrang dari pinggir jalan (x=±4) ke sisi lain.
    """
    WARNA_BAJU = [
        (0.8, 0.1, 0.1), (0.1, 0.5, 0.8), (0.1, 0.7, 0.2),
        (0.8, 0.6, 0.1), (0.5, 0.1, 0.7), (0.9, 0.4, 0.2),
    ]

    def __init__(self, idx, zc):
        """
        idx  : nomor urut (0..N-1) untuk offset posisi Z
        zc   : z-center zebra crossing (±7.0)
        """
        self.zc     = zc            # z tengah zebra
        self.x      = -4.0          # mulai dari trotoar kiri
        self.speed  = 1.0 + (idx % 3) * 0.25
        self.phase  = idx * 0.33    # fase langkah (0..1)
        self.ukuran = 0.85 + (idx % 3) * 0.08
        # Offset Z dalam zebra agar tidak tumpuk
        self.z_off  = (idx - 1) * 0.55
        self.warna_idx = idx % len(self.WARNA_BAJU)
        self.aktif  = False         # aktif = sedang menyebrang
        self.sudah_selesai = False  # sudah nyebrang di siklus ini
        self._reset()

    def _reset(self):
        self.x = -4.2
        self.aktif = False
        self.sudah_selesai = True   # tunggu lampu hijau dulu sebelum boleh nyebrang lagi

    def update(self, dt, lampu_merah):
        """Pejalan kaki nyebrang sekali per siklus merah, lalu berhenti."""
        # Jika fase bukan boleh_nyebrang lagi (palang mulai buka), paksa berhenti
        if not lampu_merah:
            if self.aktif:
                self._reset()   # masuk trotoar, beri jalan ke kendaraan
            self.sudah_selesai = False  # siap untuk siklus berikutnya
            return

        # Mulai nyebrang hanya jika belum nyebrang di siklus ini
        if not self.aktif and not self.sudah_selesai:
            self.aktif = True
            self.x = -4.2

        if self.aktif:
            self.x += self.speed * dt
            self.phase = (self.phase + dt * self.speed * 1.8) % 1.0
            if self.x > 4.5:
                self._reset()   # selesai satu kali, tidak loop lagi

    def draw(self):
        if not self.aktif:
            return
        # Putar 90° agar menghadap arah menyebrang (sumbu X)
        bj = self.WARNA_BAJU[self.warna_idx]
        glPushMatrix()
        glTranslatef(self.x, 0, self.zc + self.z_off)
        glRotatef(90, 0, 1, 0)   # hadap ke +X (arah menyebrang)
        draw_pejalan_kaki(0, 0, self.phase, self.ukuran)
        glPopMatrix()


def buat_kendaraan():
    """Buat daftar kendaraan (mobil + motor) di kedua jalur."""
    kd = []
    # Jalur kiri (x=-1.5): bergerak ke +z
    specs_kiri = [
        (-22,'mobil',0), (-13,'motor',2), (-4,'mobil',4),
        (5,'mobil',1),  (14,'motor',3),  (23,'mobil',6)
    ]
    # Jalur kanan (x=+1.5): bergerak ke -z
    specs_kanan = [
        (22,'mobil',5), (13,'motor',1),  (4,'mobil',2),
        (-5,'motor',0), (-14,'mobil',3), (-23,'mobil',6)
    ]
    for z,t,w in specs_kiri:
        kd.append(Kendaraan(z,-1.5,t,w))
    for z,t,w in specs_kanan:
        kd.append(Kendaraan(z, 1.5,t,w))
    return kd


def buat_pejalan_kaki():
    """Buat beberapa pejalan kaki di kedua zebra crossing."""
    pejalan = []
    # Zebra di z=+7.0 (sisi utara)
    for i in range(4):
        pejalan.append(PejalanKaki(i, 7.0))
    # Zebra di z=-7.0 (sisi selatan)
    for i in range(4):
        pk = PejalanKaki(i, -7.0)
        pk.speed *= -1 if i % 2 == 0 else 1  # variasi arah
        pejalan.append(pk)
    return pejalan



class KendaraanCabang:
    """Kendaraan di jalan cabang (bergerak di sumbu X, bukan Z)."""
    def __init__(self, x, z_jalur, tipe, warna, arah_x):
        self.x     = float(x)
        self.z     = float(z_jalur)   # z tetap (di jalan cabang)
        self.tipe  = tipe
        self.warna = warna
        self.arah  = arah_x           # +1 atau -1 di sumbu X
        self.speed = 3.5 if tipe == 'mobil' else 4.2

    def update(self, dt):
        self.x += self.arah * self.speed * dt
        # Wrap-around di sumbu X
        if self.x >  32: self.x = -32
        if self.x < -32: self.x =  32

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        # Kendaraan cabang menghadap sumbu X → rotate 90°
        if self.arah == 1:
            glRotatef(-90, 0, 1, 0)
        else:
            glRotatef(90, 0, 1, 0)
        if self.tipe == 'mobil':
            draw_mobil(0, 0, self.warna)
        else:
            draw_motor_obj(0, 0, self.warna)
        glPopMatrix()


def buat_kendaraan_cabang():
    kd = []
    # Jalan cabang z=-28 (utara): jalur kiri z=-27 arah+X, jalur kanan z=-29 arah-X
    specs_utara_kiri  = [(-25,'mobil',0),(-10,'motor',2),(5,'mobil',4),(20,'mobil',1)]
    specs_utara_kanan = [(25,'mobil',5),(10,'motor',3),(-5,'mobil',2),(-20,'mobil',6)]
    for x,t,w in specs_utara_kiri:
        kd.append(KendaraanCabang(x, -27.5, t, w, +1))
    for x,t,w in specs_utara_kanan:
        kd.append(KendaraanCabang(x, -28.5, t, w, -1))
    # Jalan cabang z=+28 (selatan): jalur kiri z=+27.5 arah+X, jalur kanan z=+28.5 arah-X
    specs_sel_kiri  = [(15,'mobil',1),(-5,'motor',3),(-20,'mobil',5),(28,'mobil',0)]
    specs_sel_kanan = [(-15,'mobil',2),(5,'motor',4),(22,'mobil',6),(-28,'mobil',3)]
    for x,t,w in specs_sel_kiri:
        kd.append(KendaraanCabang(x, 27.5, t, w, +1))
    for x,t,w in specs_sel_kanan:
        kd.append(KendaraanCabang(x, 28.5, t, w, -1))
    return kd

# ═══════════════════════════════════════════════
#  SISTEM KAMERA
# ═══════════════════════════════════════════════

# ── Dimensi geometri kendaraan (harus sinkron dengan draw_mobil / draw_motor_obj) ──
# Mobil: panjang bodi Z = 2.2, kaca depan di z_lokal ≈ +0.82 (arah +z = maju)
#        atap bodi  Y_max ≈ 0.32 + 0.52/2 + 0.45 = ~1.04
# Motor: panjang Z  = 1.1, setang di z_lokal ≈ +0.48, kepala pengendara Y ≈ 1.32
_MOBIL = dict(
    # eye offset dari pusat bodi kendaraan (koordinat lokal, sebelum rotasi)
    eye_y     =  0.88,   # tinggi mata pengemudi (dalam bodi, di atas kursi)
    eye_z_fwd =  0.65,   # maju dari tengah → mendekati kaca depan (z_lokal kaca ≈ 0.82)
    # target offset — jauh ke depan agar gluLookAt selalu menghadap luar
    tgt_z_fwd = 15.0,    # 15 unit di depan kendaraan (world space)
    tgt_y_dip = -0.10,   # sedikit ke bawah (melihat permukaan jalan sedikit)
)
_MOTOR = dict(
    eye_y     =  1.10,   # tinggi mata pengendara (kepala pengendara Y ≈ 1.32, ambil sedikit lebih rendah)
    eye_z_fwd =  0.35,   # maju dari tengah → mendekati handlebar (z_lokal setang ≈ 0.48)
    tgt_z_fwd = 15.0,
    tgt_y_dip = -0.08,
)


class CameraSystem:
    """
    Mengelola 3 mode kamera:
      CAM_OVERVIEW  – sudut pandang atas bebas (putar + zoom)
      CAM_DRIVER    – POV dashcam dari dalam kendaraan yang dipilih,
                      menghadap ke luar (jalan, palang, rel)
      CAM_TRACKSIDE – dari pinggir rel (sudut tetap)

    Keyboard:
      1 / 2 / 3  → ganti mode
      TAB / N    → (mode driver) kendaraan berikutnya
      P          → (mode driver) kendaraan sebelumnya
      +/-        → zoom (mode overview)
      ESC        → tutup window
    Mouse:
      Drag kiri  → putar (mode overview)
      Scroll     → zoom (mode overview)
    """

    def __init__(self):
        self.mode        = CAM_OVERVIEW
        # Overview params
        self.yaw         = 45.0
        self.pitch       = 35.0
        self.dist        = 25.0
        self._mx         = 0.0
        self._my         = 0.0
        self._mdown      = False
        # State interpolasi smooth (eye, center, up)
        self._eye        = [0.0, 25.0, 0.0]
        self._center     = [0.0,  0.0,  0.0]
        self._up         = [0.0,  1.0,  0.0]
        self._smooth_ov  = 0.10   # overview: halus
        self._smooth_drv = 0.20   # driver: lebih responsif agar ikut kendaraan
        # Indeks kendaraan aktif untuk driver mode
        self._driver_idx = 0

    # ══════════════════════════════════════════
    #  INPUT CALLBACKS
    # ══════════════════════════════════════════
    def on_key(self, window, key, sc, act, mod, kendaraan_list=None):
        if kendaraan_list is None:
            kendaraan_list = []
        if act in (glfw.PRESS, glfw.REPEAT):
            if key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(window, True)
            elif key == glfw.KEY_1:
                self.mode = CAM_OVERVIEW
                print("[CAM] Mode 1 – Overview")
            elif key == glfw.KEY_2:
                self.mode = CAM_DRIVER
                self._log_target(kendaraan_list)
                print("       TAB/N = kendaraan berikutnya  |  P = sebelumnya")
            elif key == glfw.KEY_3:
                self.mode = CAM_TRACKSIDE
                print("[CAM] Mode 3 – Trackside")
            elif key == glfw.KEY_EQUAL:
                self.dist = max(5.0, self.dist - 1.5)
            elif key == glfw.KEY_MINUS:
                self.dist = min(50.0, self.dist + 1.5)
            # Ganti kendaraan target (hanya aktif saat driver mode)
            elif key in (glfw.KEY_TAB, glfw.KEY_N) and self.mode == CAM_DRIVER:
                self._driver_idx = (self._driver_idx + 1) % max(1, len(kendaraan_list))
                self._log_target(kendaraan_list)
            elif key == glfw.KEY_P and self.mode == CAM_DRIVER:
                self._driver_idx = (self._driver_idx - 1) % max(1, len(kendaraan_list))
                self._log_target(kendaraan_list)

    def _log_target(self, kendaraan_list):
        if not kendaraan_list:
            return
        idx = self._driver_idx % len(kendaraan_list)
        k   = kendaraan_list[idx]
        sisi = 'kiri' if k.x < 0 else 'kanan'
        print(f"[CAM] Driver  → #{idx+1}/{len(kendaraan_list)}"
              f"  {k.tipe.upper()}  jalur-{sisi}"
              f"  arah={'→+Z' if k.arah==1 else '→-Z'}")

    def on_mouse_button(self, window, button, act, mod):
        if button == glfw.MOUSE_BUTTON_LEFT:
            self._mdown = (act == glfw.PRESS)
            if self._mdown:
                self._mx, self._my = glfw.get_cursor_pos(window)

    def on_cursor(self, window, xpos, ypos):
        if self._mdown and self.mode == CAM_OVERVIEW:
            self.yaw   += (xpos - self._mx) * 0.4
            self.pitch  = max(5.0, min(85.0, self.pitch + (ypos - self._my) * 0.3))
            self._mx, self._my = xpos, ypos

    def on_scroll(self, window, xoff, yoff):
        if self.mode == CAM_OVERVIEW:
            self.dist = max(5.0, min(50.0, self.dist - yoff * 1.0))

    # ══════════════════════════════════════════
    #  KALKULASI TARGET KAMERA
    # ══════════════════════════════════════════
    def _target_overview(self):
        pr = math.radians(self.pitch)
        yr = math.radians(self.yaw)
        cx = self.dist * math.cos(pr) * math.sin(yr)
        cy = self.dist * math.sin(pr)
        cz = self.dist * math.cos(pr) * math.cos(yr)
        return [cx, cy, cz], [0.0, 0.5, 0.0], [0.0, 1.0, 0.0]

    def _target_driver(self, kendaraan_list):
        """
        POV dashcam yang benar — menghadap ke luar kendaraan.

        Analisis geometri kendaraan (koordinat lokal, Y-up, +Z = depan kendaraan):
          • Bodi bawah : z ∈ [-1.1, +1.1]  (setengah panjang 2.2)
          • Kaca depan  : z_lokal ≈ +0.82
          • Bodi atas   : y ≈ 0.32 .. 1.04

        Strategi anti-clipping:
          1. eye_z_fwd < 0.82 → eye masih di dalam bodi (di belakang kaca depan) ✓
          2. near-plane projection dipakai oleh OpenGL utk clipping, bukan geometri.
             Karena near = 0.1, objek < 0.1 dari eye terpotong.
             Kita pastikan forward distance ke kaca ≥ 0.1:
               gap = 0.82 - eye_z_fwd = 0.82 - 0.65 = 0.17  → aman ✓
          3. target jauh (15 unit) → gluLookAt memandang ke luar, bukan ke dalam.

        Koordinat world:
          • kendaraan berada di (k.x, 0, k.z)
          • arah gerak  : +Z jika k.arah == +1, -Z jika k.arah == -1
          • forward_vec = (0, 0, k.arah)   (sudah dalam world space karena
            rotasi hanya di sumbu Y dan draw() menerapkan glRotatef 180 pada
            kendaraan arah -1, sehingga +Z lokal = k.arah di world)
        """
        if not kendaraan_list:
            return self._target_overview()

        idx    = self._driver_idx % len(kendaraan_list)
        k      = kendaraan_list[idx]
        cfg    = _MOBIL if k.tipe == 'mobil' else _MOTOR

        # ── forward vector (world space) ─────────────────────────────────────
        #   arah +1  →  kendaraan bergerak ke +Z  →  forward = (0, 0, +1)
        #   arah -1  →  kendaraan bergerak ke -Z  →  forward = (0, 0, -1)
        fwd_z = float(k.arah)   # ±1

        # ── posisi eye (dalam bodi, di depan kursi pengemudi) ────────────────
        #   Offset eye_z_fwd ke arah depan kendaraan (mendekati kaca depan).
        #   Tetap di dalam bodi (< setengah panjang bodi = 1.1) sehingga
        #   tidak menembus kaca → tidak ada geometri di antara eye dan luar.
        eye = [
            k.x,                              # X: tetap di jalur kendaraan
            cfg['eye_y'],                     # Y: tinggi mata pengemudi
            k.z + fwd_z * cfg['eye_z_fwd'],   # Z: mundur sedikit dari kaca depan
        ]

        # ── titik pandang (target) ────────────────────────────────────────────
        #   Diletakkan jauh di depan (tgt_z_fwd unit) dalam world space.
        #   Sedikit lebih rendah dari eye agar melihat ke permukaan jalan.
        #   Karena target sangat jauh, gluLookAt dipastikan memandang ke luar.
        target_pt = [
            k.x,                                           # X: lurus
            cfg['eye_y'] + cfg['tgt_y_dip'],               # Y: sedikit ke bawah
            k.z + fwd_z * cfg['tgt_z_fwd'],                # Z: jauh ke depan
        ]

        up = [0.0, 1.0, 0.0]
        return eye, target_pt, up

    def _target_trackside(self):
        """Kamera dari pinggir rel, menghadap ke arah kereta lewat."""
        return [12.0, 3.5, -8.0], [0.0, 1.0, 0.0], [0.0, 1.0, 0.0]

    # ══════════════════════════════════════════
    #  APPLY KE OPENGL
    # ══════════════════════════════════════════
    def apply(self, kendaraan_list):
        """Hitung posisi kamera, interpolasi smooth, lalu terapkan gluLookAt."""
        if self.mode == CAM_OVERVIEW:
            eye_t, cen_t, up_t = self._target_overview()
            smooth = self._smooth_ov
        elif self.mode == CAM_DRIVER:
            eye_t, cen_t, up_t = self._target_driver(kendaraan_list)
            smooth = self._smooth_drv
        else:
            eye_t, cen_t, up_t = self._target_trackside()
            smooth = self._smooth_ov

        # Interpolasi lerp per komponen
        for i in range(3):
            self._eye[i]    = lerp(self._eye[i],    eye_t[i],  smooth)
            self._center[i] = lerp(self._center[i], cen_t[i],  smooth)
            self._up[i]     = lerp(self._up[i],     up_t[i],   smooth)

        glLoadIdentity()
        glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 20.0, 10.0, 1.0])
        gluLookAt(
            self._eye[0],    self._eye[1],    self._eye[2],
            self._center[0], self._center[1], self._center[2],
            self._up[0],     self._up[1],     self._up[2],
        )

    def mode_str(self):
        return {
            CAM_OVERVIEW:  '1-Overview',
            CAM_DRIVER:    f'2-Driver[#{self._driver_idx+1}]',
            CAM_TRACKSIDE: '3-Trackside',
        }.get(self.mode, '?')


# ═══════════════════════════════════════════════
#  STATE ANIMASI
# ═══════════════════════════════════════════════
class SimState:
    """Semua state simulasi dalam satu kelas."""
    def __init__(self):
        self.fase      = FASE_IDLE
        self.ftimer    = 0.0
        self.kereta_x  = 55.0
        self.palang    = 90.0    # sudut (90=buka, 0=tutup)
        self.merah     = False
        self.paused    = False
        self.speed_mul = 1.0     # pengali kecepatan

    @property
    def palang_tutup(self):
        return self.fase in (FASE_TUTUP, FASE_KERETA, FASE_BUKA)

    def update(self, dt):
        if self.paused:
            return
        dt *= self.speed_mul
        self.ftimer += dt

        if self.fase == FASE_IDLE:
            self.merah    = False
            self.palang   = 90.0
            self.kereta_x = 55.0
            if self.ftimer > 6.0:   # idle 6 detik, kendaraan jalan bebas
                self.fase = FASE_TUTUP; self.ftimer = 0.0

        elif self.fase == FASE_TUTUP:
            # Lampu merah nyala DULUAN saat palang mulai tutup
            # → kendaraan berhenti di stop line sebelum palang benar-benar nutup
            self.merah  = True
            self.palang = lerp(90.0, 0.0, self.ftimer / 4.0)  # 4 detik tutup (lebih lambat)
            if self.ftimer > 4.0:
                self.fase = FASE_KERETA; self.ftimer = 0.0; self.palang = 0.0

        elif self.fase == FASE_KERETA:
            self.merah    = True
            self.palang   = 0.0
            self.kereta_x -= 14.0 * dt
            if self.kereta_x < -30.0:
                self.fase = FASE_BUKA; self.ftimer = 0.0

        elif self.fase == FASE_BUKA:
            self.merah  = True   # tetap merah sampai palang benar-benar terbuka
            self.palang = lerp(0.0, 90.0, self.ftimer / 4.0)  # 4 detik buka (lebih lambat)
            self.kereta_x -= 14.0 * dt
            if self.ftimer > 4.0:
                self.fase = FASE_IDLE; self.ftimer = 0.0
                self.merah = False; self.palang = 90.0; self.kereta_x = 55.0


# ═══════════════════════════════════════════════
#  HUD (Heads-Up Display)
# ═══════════════════════════════════════════════
def draw_hud_text(win, sim, cam):
    """Print info ke konsol setiap beberapa detik (OpenGL tanpa font)."""
    pass  # Info sudah dicantumkan di title bar via glfw.set_window_title

def update_title(win, sim, cam):
    fase_names = {FASE_IDLE:'IDLE',FASE_TUTUP:'TUTUP',FASE_KERETA:'KERETA',FASE_BUKA:'BUKA'}
    status = "⏸ PAUSED |" if sim.paused else f"▶ x{sim.speed_mul:.1f} |"
    title = (f"Sim Perlintasan KA  |  {status}"
             f"  Fase:{fase_names[sim.fase]}  |"
             f"  CAM:{cam.mode_str()}  |"
             f"  [1/2/3]=Kamera  [TAB/N/P]=Pilih Kendaraan  [SPACE]=Pause  [F/S]=Speed")
    glfw.set_window_title(win, title)


# ═══════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════
def main():
    if not glfw.init():
        raise RuntimeError("GLFW init gagal")

    win = glfw.create_window(1200, 700, "Simulasi Perlintasan Kereta Api 3D", None, None)
    if not win:
        glfw.terminate()
        raise RuntimeError("Window gagal dibuat")
    glfw.make_context_current(win)

    # ── Inisialisasi objek state ──────────────
    sim = SimState()
    cam = CameraSystem()
    kendaraan = buat_kendaraan()
    pejalan   = buat_pejalan_kaki()
    kend_cabang = buat_kendaraan_cabang()

    # ── Callback resize ───────────────────────
    def on_resize(w, width, height):
        if height == 0: height = 1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(60, width/height, 0.05, 300.0)
        glMatrixMode(GL_MODELVIEW)
    glfw.set_framebuffer_size_callback(win, on_resize)

    # ── Callback keyboard ─────────────────────
    def on_key(w, key, sc, act, mod):
        cam.on_key(w, key, sc, act, mod, kendaraan_list=kendaraan)
        if act in (glfw.PRESS,):
            if key == glfw.KEY_SPACE:
                sim.paused = not sim.paused
                print("[SIM] " + ("Paused" if sim.paused else "Resumed"))
            elif key == glfw.KEY_F:
                sim.speed_mul = min(4.0, sim.speed_mul + 0.5)
                print(f"[SIM] Speed x{sim.speed_mul:.1f}")
            elif key == glfw.KEY_S:
                sim.speed_mul = max(0.5, sim.speed_mul - 0.5)
                print(f"[SIM] Speed x{sim.speed_mul:.1f}")

    glfw.set_key_callback(win, on_key)
    glfw.set_mouse_button_callback(win, cam.on_mouse_button)
    glfw.set_cursor_pos_callback(win, cam.on_cursor)
    glfw.set_scroll_callback(win, cam.on_scroll)

    # ── OpenGL setup ──────────────────────────
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH); glEnable(GL_NORMALIZE)
    glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.40, 0.40, 0.38, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.90, 0.88, 0.80, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.30, 0.30, 0.30, 1.0])
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60, 1200/700, 0.05, 300.0)
    glMatrixMode(GL_MODELVIEW)

    print("=" * 65)
    print(" Simulasi Perlintasan Kereta Api 3D")
    print("=" * 65)
    print(" [1] Overview   [2] Driver POV   [3] Trackside")
    print(" [TAB/N] Kendaraan berikutnya   [P] Kendaraan sebelumnya")
    print(" [SPACE] Pause/Resume   [F] Speed Up   [S] Slow Down")
    print(" DRAG = putar kamera   SCROLL = zoom   [ESC] = Keluar")
    print("=" * 65)

    prev_time = time.time()
    title_timer = 0.0

    while not glfw.window_should_close(win):
        now = time.time()
        dt  = min(now - prev_time, 0.05)
        prev_time = now

        glfw.poll_events()

        # ── Update state ──────────────────────
        sim.update(dt)

        # Update kendaraan cabang
        for kc in kend_cabang:
            kc.update(dt)

        # Update pejalan kaki - hanya nyebrang saat fase KERETA (palang tutup sempurna)
        boleh_nyebrang = (sim.fase == FASE_KERETA)
        for pk in pejalan:
            pk.update(dt, boleh_nyebrang)

        # Update kendaraan - urutkan berdasarkan posisi terdepan per jalur
        jalur_kiri  = sorted([k for k in kendaraan if k.x < 0], key=lambda k:  k.z)  # arah+1 → z terbesar duluan
        jalur_kanan = sorted([k for k in kendaraan if k.x > 0], key=lambda k: -k.z)  # arah-1 → z terkecil duluan
        for jalur in (jalur_kiri, jalur_kanan):
            for i, k in enumerate(jalur):
                depan = jalur[i+1] if i < len(jalur)-1 else None
                k.update(dt, sim.palang_tutup, depan.z if depan else None, pejalan_list=pejalan)

        # Update title bar
        title_timer += dt
        if title_timer > 0.5:
            title_timer = 0.0
            update_title(win, sim, cam)

        # ── Render ───────────────────────────
        w, h = glfw.get_framebuffer_size(win)
        glViewport(0, 0, w, h)
        glClearColor(0.52, 0.78, 0.92, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        cam.apply(kendaraan)

        draw_jalan()
        draw_jalan_cabang()
        draw_zebra_dan_trotoar()
        draw_rel()
        draw_portal(sim.palang, sim.merah)
        draw_bangunan()
        # Driver mode: skip menggambar kendaraan yg kamera ada di dalamnya
        driver_idx = cam._driver_idx % len(kendaraan) if kendaraan else -1
        for i, k in enumerate(kendaraan):
            if cam.mode == CAM_DRIVER and i == driver_idx:
                continue
            k.draw()
        if sim.fase in (FASE_TUTUP, FASE_KERETA, FASE_BUKA):
            draw_kereta(sim.kereta_x)

        # Gambar kendaraan cabang
        for kc in kend_cabang:
            kc.draw()

        # Gambar pejalan kaki
        for pk in pejalan:
            pk.draw()

        glfw.swap_buffers(win)

    glfw.terminate()
    print("Simulasi selesai.")


if __name__ == "__main__":
    main()