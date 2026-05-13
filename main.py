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
CAM_FREE       = 4

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
    box(0,-0.05, 0, 100,0.10,70,  0.25,0.45,0.18)
    box(0, 0.02, 0, 100,0.04,3.5, 0.48,0.46,0.44)
    box(0, 0.03, 0, 8.0,0.06,70,  0.20,0.20,0.22)
    for i in range(-17,18):
        zi = i * 2.0
        if abs(zi) < 4.5: continue          # area rel
        if 5.0 <= abs(zi) <= 9.0: continue  # area zebra cross (z=±7)
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
    trot  = (0.68, 0.66, 0.63)

    for zc in (-28.0, 28.0):
        # Badan jalan cabang (sumbu X, lebar 6, panjang 60)
        # Jalan cabang kiri (x negatif), skip area jalan utama
        box(-26, 0.04, zc, 44, 0.06, 6.0, *aspal)   # x: -48 s/d -4
        # Jalan cabang kanan (x positif), skip area jalan utama
        box( 26, 0.04, zc, 44, 0.06, 6.0, *aspal)   # x: +4 s/d +48
        # Bahu jalan / shoulder
       # Bahu kiri
        box(-26, 0.035, zc-3.2, 44, 0.04, 0.6, *bahu)
        box(-26, 0.035, zc+3.2, 44, 0.04, 0.6, *bahu)
        # Bahu kanan
        box( 26, 0.035, zc-3.2, 44, 0.04, 0.6, *bahu)
        box( 26, 0.035, zc+3.2, 44, 0.04, 0.6, *bahu)
        # Marka tengah kiri
        for xi in range(-14, 15):
            xi2 = xi * 2.2
            if -4 < xi2 < 4: continue   # skip area jalan utama
            if 4.0 < abs(xi2) < 7.0: continue  # skip area zebra cross (x=±5.25)
            box(xi2, 0.08, zc, 1.0, 0.01, 0.15, *marka)
        # Marka tepi kiri & kanan (skip tengah)
        for sign_x in (-1, 1):
            box(sign_x * 26, 0.075, zc-2.6, 40, 0.01, 0.12, *marka)
            box(sign_x * 26, 0.075, zc+2.6, 40, 0.01, 0.12, *marka)

        # Trotoar sisi jalan cabang — skip area persimpangan (x=±8)
        gap_x = 8.0
        pjg_x = 30.0 - gap_x
        for sign in (-1, 1):
            xc_seg = sign * (gap_x + pjg_x) / 2
            box(xc_seg, 0.11, zc-4.0, pjg_x, 0.22, 2.0, *trot)
            box(xc_seg, 0.11, zc+4.0, pjg_x, 0.22, 2.0, *trot)

        # Trotoar penyambung di area persimpangan jalan utama (x=±5.25, gap z=±3)
        # Ini menyambung trotoar jalan utama melewati persimpangan jalan cabang
        for tx in (-5.25, 5.25):
            box(tx, 0.12, zc, 1.5, 0.24, 6.0, *trot)   # sambungan trotoar jalan utama di persimpangan
        # Kerb penyambung
        kerb = (0.45, 0.43, 0.41)
        for kx in (-4.05, 4.05):
            box(kx, 0.06, zc, 0.12, 0.14, 6.0, *kerb)

        # Pohon di pinggir jalan cabang (tiap 4 unit)
        for xi in range(-13, 14, 4):
            if abs(xi) < 5: continue   # jangan tumbuh di persimpangan
            draw_pohon(xi, zc - 5.5)
            draw_pohon(xi, zc + 5.5)

    # ── Jalan penghubung / on-ramp kiri (x=-20, menyambung jalan utama ke cabang) ──
    for xc in (-20.0, 20.0):
        # Ramp vertikal (sumbu Z) menghubungkan jalan utama ke jalan cabang
        box(xc, 0.04, 0, 4.0, 0.06, 56, *aspal)
        # Marka tepi ramp
        box(xc-1.8, 0.065, 0, 0.12, 0.01, 46, *marka)
        box(xc+1.8, 0.065, 0, 0.12, 0.01, 46, *marka)
        # Marka tengah putus-putus ramp
        for zi in range(-13, 14):
            zi2 = zi * 2.0
            if abs(zi2) < 3: continue
            if abs(zi2) > 23: continue   # skip area jalan cabang
            box(xc, 0.07, zi2, 0.12, 0.01, 1.0, *marka)
        # Trotoar ramp — dibagi dua, skip area persimpangan jalan utama (z=±8)
        gap_z = 8.0
        pjg   = 28.0 - gap_z
        for sign in (-1, 1):
            zc_seg = sign * (gap_z + pjg) / 2
            box(xc-2.8, 0.11, zc_seg, 1.2, 0.22, pjg, *trot)
            box(xc+2.8, 0.11, zc_seg, 1.2, 0.22, pjg, *trot)
        # Trotoar penyambung di area persimpangan jalan utama (z=0)
        box(xc-2.8, 0.11, 0, 1.2, 0.22, 16.0, *trot)
        box(xc+2.8, 0.11, 0, 1.2, 0.22, 16.0, *trot)
        # Pohon di ramp
        for zi in range(-12, 13, 5):
            if abs(zi) < 4: continue
            draw_pohon(xc - 4.0, zi)
            draw_pohon(xc + 4.0, zi)

def draw_rel():
    for i in range(-33,34):
        box(i*1.5, 0.22, 0, 1.2,0.12,1.8, 0.40,0.25,0.10)
    box(0,0.35,-0.7, 100,0.10,0.15, 0.6,0.6,0.65)
    box(0,0.41,-0.7, 100,0.05,0.22, 0.7,0.7,0.75)
    box(0,0.35, 0.7, 100,0.10,0.15, 0.6,0.6,0.65)
    box(0,0.41, 0.7, 100,0.05,0.22, 0.7,0.7,0.75)
    

def draw_terowongan():
    tx = 54.0   
    tz = 0.0 

    # Gundukan bukit 
    box(tx + 5, 0.5, tz,  18, 8, 13.0, 0.50, 0.48, 0.45)
    box(tx + 5, 1.5, tz,  15, 9, 11, 0.50, 0.48, 0.45)
    box(tx + 5, 2.5, tz,  11, 10, 8, 0.50, 0.48, 0.45)
    box(tx + 5, 3.2, tz,   8, 11, 5, 0.50, 0.48, 0.45)

    # Terowongan di sisi X positif (arah kereta muncul)
    tx = 50.0

    # Tembok atas & bawah portal (sumbu Z karena kereta lewat di sumbu X)
    box(tx, 1.5, -2.5, 2.0, 3.0, 1.0, 0.22, 0.22, 0.22)
    box(tx, 1.5,  2.5, 2.0, 3.0, 1.0, 0.22, 0.22, 0.22)

    # Atap portal
    box(tx, 3.2, 0, 2.0, 0.8, 6.0, 0.22, 0.22, 0.22)

    # Lubang gelap
    box(tx + 1.0, 1.5, 0, 2.5, 3.0, 5.0, 0.05, 0.05, 0.05)

    # Detail batu
    for bz in [-1.8, -0.6, 0.6, 1.8]:
        box(tx, 3.0, bz, 1.8, 0.4, 1.0, 0.50, 0.45, 0.38)

# ═══════════════════════════════════════════════
#  CAR FREE DAY / BAZAAR
# ═══════════════════════════════════════════════

def draw_tenda_warung(cx, cy, cz, rot_y=0, warna_tenda=(0.9,0.2,0.15)):
    """Tenda warung/stan bazaar: meja + atap tenda segitiga."""
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glRotatef(rot_y, 0, 1, 0)
    r, g, b = warna_tenda

    # Meja kayu
    box(0, 0.50, 0,   1.8, 0.08, 0.9,  0.55, 0.35, 0.15)
    # Kaki meja (4 tiang)
    for kx, kz in [(-0.82, 0.38), (0.82, 0.38), (-0.82, -0.38), (0.82, -0.38)]:
        tiang_vertikal(kx, 0.0, kz, 0.04, 0.50, 6, 0.40, 0.25, 0.10)

    # Tiang tenda (2 tiang di belakang)
    tiang_vertikal(-0.85, 0.50, -0.38, 0.05, 2.0, 6, 0.55, 0.35, 0.15)
    tiang_vertikal( 0.85, 0.50, -0.38, 0.05, 2.0, 6, 0.55, 0.35, 0.15)
    # Tiang tenda (2 tiang di depan - lebih pendek, atap miring)
    tiang_vertikal(-0.85, 0.50,  0.38, 0.05, 1.50, 6, 0.55, 0.35, 0.15)
    tiang_vertikal( 0.85, 0.50,  0.38, 0.05, 1.50, 6, 0.55, 0.35, 0.15)

    # Atap tenda (miring depan-belakang) - pakai quads
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    # permukaan atas
    glNormal3f(0, 1, 0.3)
    glVertex3f(-0.95, 2.50, -0.48)
    glVertex3f( 0.95, 2.50, -0.48)
    glVertex3f( 0.95, 2.00,  0.48)
    glVertex3f(-0.95, 2.00,  0.48)
    glEnd()
    # Sisi-sisi tenda
    glColor3f(r*0.85, g*0.85, b*0.85)
    glBegin(GL_QUADS)
    # Sisi kiri
    glNormal3f(-1, 0, 0)
    glVertex3f(-0.95, 2.50, -0.48); glVertex3f(-0.95, 2.00, 0.48)
    glVertex3f(-0.95, 1.50, 0.48);  glVertex3f(-0.95, 2.00, -0.48)
    # Sisi kanan
    glNormal3f(1, 0, 0)
    glVertex3f( 0.95, 2.50, -0.48); glVertex3f( 0.95, 2.00, -0.48)
    glVertex3f( 0.95, 1.50,  0.48); glVertex3f( 0.95, 2.00,  0.48)
    # Sisi belakang
    glNormal3f(0, 0, -1)
    glVertex3f(-0.95, 2.50, -0.48); glVertex3f( 0.95, 2.50, -0.48)
    glVertex3f( 0.95, 2.00, -0.48); glVertex3f(-0.95, 2.00, -0.48)
    glEnd()

    # Barang di atas meja (kotak-kotak kecil = produk/makanan)
    box(-0.55, 0.60, 0.0,  0.35, 0.20, 0.25, 0.9, 0.7, 0.2)  # kuning - jajanan
    box( 0.10, 0.60, 0.1,  0.30, 0.25, 0.22, 0.8, 0.3, 0.2)  # oranye - makanan
    box( 0.55, 0.60,-0.1,  0.28, 0.18, 0.28, 0.3, 0.7, 0.4)  # hijau - minuman
    # Wadah/baskom
    silinder(0.0, 0.58, -0.2, 0.18, 0.10, 8, 0.70, 0.65, 0.55)
    glPopMatrix()


def draw_orang_berdiri(cx, cz, rot_y=0, warna=(0.3, 0.5, 0.8)):
    """Figur orang sederhana sedang berdiri/berbelanja."""
    glPushMatrix()
    glTranslatef(cx, 0, cz)
    glRotatef(rot_y, 0, 1, 0)
    r, g, b = warna
    # Badan
    box(0, 0.70, 0, 0.24, 0.42, 0.18, r, g, b)
    # Kepala
    bola(0, 1.05, 0, 0.13, cr=0.88, cg=0.72, cb=0.55)
    # Kaki
    box(-0.07, 0.22, 0, 0.10, 0.38, 0.12, 0.2, 0.2, 0.4)
    box( 0.07, 0.22, 0, 0.10, 0.38, 0.12, 0.2, 0.2, 0.4)
    # Tangan
    box(-0.20, 0.78, 0, 0.08, 0.30, 0.09, r*0.85, g*0.85, b*0.85)
    box( 0.20, 0.78, 0, 0.08, 0.30, 0.09, r*0.85, g*0.85, b*0.85)
    glPopMatrix()


def draw_balon(cx, cz, r_col, g_col, b_col):
    """Balon dekorasi CFD."""
    tiang_vertikal(cx, 0.0, cz, 0.015, 2.0, 5, 0.8, 0.8, 0.8)
    bola(cx, 2.25, cz, 0.22, cr=r_col, cg=g_col, cb=b_col)


def draw_spanduk_cfd(cx, cy, cz, panjang=4.0, rot_y=0):
    """Spanduk horizontal bertuliskan CAR FREE DAY."""
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glRotatef(rot_y, 0, 1, 0)
    # Tiang kiri & kanan
    tiang_vertikal(-panjang/2, 0.0, 0, 0.06, 3.2, 6, 0.55, 0.35, 0.15)
    tiang_vertikal( panjang/2, 0.0, 0, 0.06, 3.2, 6, 0.55, 0.35, 0.15)
    # Banner / kain
    box(0, 3.0, 0, panjang, 0.55, 0.08, 0.95, 0.82, 0.05)  # kuning emas
    box(0, 3.0, 0, panjang, 0.55, 0.06, 0.90, 0.75, 0.02)
    # Strip merah-putih (bendera)
    box(0, 3.20, 0, panjang-0.1, 0.12, 0.09, 0.9, 0.1, 0.1)
    box(0, 2.88, 0, panjang-0.1, 0.12, 0.09, 0.9, 0.9, 0.9)
    glPopMatrix()


def draw_kursi_dan_meja_kecil(cx, cz, rot_y=0):
    """Meja kecil dengan 2 kursi untuk pengunjung."""
    glPushMatrix()
    glTranslatef(cx, 0, cz)
    glRotatef(rot_y, 0, 1, 0)
    # Meja bundar (silinder pipih)
    silinder(0, 0.68, 0, 0.38, 0.06, 12, 0.60, 0.45, 0.25)
    tiang_vertikal(0, 0, 0, 0.05, 0.68, 6, 0.45, 0.30, 0.12)
    # 2 kursi kecil
    for zk in (-0.65, 0.65):
        box(0, 0.40, zk, 0.32, 0.06, 0.32, 0.55, 0.40, 0.20)
        tiang_vertikal(-0.13, 0, zk-0.13, 0.03, 0.40, 5, 0.45, 0.30, 0.12)
        tiang_vertikal( 0.13, 0, zk-0.13, 0.03, 0.40, 5, 0.45, 0.30, 0.12)
        tiang_vertikal(-0.13, 0, zk+0.13, 0.03, 0.40, 5, 0.45, 0.30, 0.12)
        tiang_vertikal( 0.13, 0, zk+0.13, 0.03, 0.40, 5, 0.45, 0.30, 0.12)
    glPopMatrix()


def draw_car_free_day():
    """
    Suasana Car Free Day HANYA di jalan cabang selatan (z=+28, sumbu X).
    Kendaraan sudah dibuang. Isi: tenda warung, pengunjung, meja kursi, balon, spanduk.
    """
    warna_tenda = [
        (0.9, 0.15, 0.15),   # merah
        (0.15, 0.45, 0.85),  # biru
        (0.15, 0.68, 0.25),  # hijau
        (0.9, 0.65, 0.10),   # kuning
        (0.7, 0.15, 0.75),   # ungu
        (0.9, 0.45, 0.10),   # oranye
    ]

    # ═══ JALAN CABANG SELATAN (z=+28, memanjang sumbu X) ═════════════
    # Area persimpangan dengan jalan utama (x=-8 s/d +8) dikosongkan untuk kendaraan.

    CLEAR_X = 9.0  # jarak bebas dari pusat persimpangan ke kanan/kiri

    # Tenda sisi luar (z=+31.2), menghadap ke dalam jalan
    for i, xpos in enumerate([-26, -19, -12, -5, 2, 9, 16, 23]):
        if abs(xpos) < CLEAR_X:
            continue  # skip area persimpangan
        draw_tenda_warung(xpos, 0, 31.2, rot_y=180, warna_tenda=warna_tenda[(i+3) % len(warna_tenda)])
        draw_orang_berdiri(xpos + 0.5, 29.8, rot_y=90,  warna=(0.6, 0.4+i*0.03, 0.2))
        draw_orang_berdiri(xpos - 0.4, 29.8, rot_y=70,  warna=(0.3, 0.5, 0.7+i*0.02))
        if i % 3 == 1:
            draw_kursi_dan_meja_kecil(xpos, 29.4, rot_y=0)

    # Tenda sisi dalam (z=+24.8), menghadap ke dalam jalan
    for i, xpos in enumerate([-24, -17, -10, -3, 4, 11, 18, 25]):
        if abs(xpos) < CLEAR_X:
            continue  # skip area persimpangan
        draw_tenda_warung(xpos, 0, 24.8, rot_y=0, warna_tenda=warna_tenda[(i+1) % len(warna_tenda)])
        draw_orang_berdiri(xpos,       26.2, rot_y=-90, warna=(0.7, 0.2, 0.5+i*0.03))
        draw_orang_berdiri(xpos + 0.6, 26.8, rot_y=-70, warna=(0.4, 0.6, 0.3+i*0.02))
        if i % 3 == 0:
            draw_kursi_dan_meja_kecil(xpos, 26.6, rot_y=0)

    # Spanduk di ujung kiri & kanan jalan cabang selatan
    draw_spanduk_cfd(-27, 0, 28, panjang=4.0, rot_y=90)
    draw_spanduk_cfd( 27, 0, 28, panjang=4.0, rot_y=90)

    # Balon warna-warni — skip area persimpangan
    balon_warna = [
        (0.9,0.2,0.2),(0.2,0.5,0.9),(0.2,0.8,0.3),
        (0.9,0.8,0.1),(0.8,0.2,0.8),(0.9,0.5,0.1),
        (0.1,0.9,0.8),(0.9,0.3,0.6),(0.6,0.9,0.1)
    ]
    for i, xb in enumerate([-28, -21, -14, -7, 0, 7, 14, 21, 28]):
        if abs(xb) < CLEAR_X:
            continue  # skip area persimpangan
        draw_balon(xb, 32.0, *balon_warna[i % len(balon_warna)])
        draw_balon(xb, 24.0, *balon_warna[(i+4) % len(balon_warna)])


# ═══════════════════════════════════════════════
#  KONSTRUKSI & DEMO RAKYAT (jalan cabang utara z=-28)
# ═══════════════════════════════════════════════

def draw_cone_lalu_lintas(cx, cz):
    """Traffic cone oranye."""
    glPushMatrix(); glTranslatef(cx, 0, cz)
    # Alas
    box(0, 0.04, 0, 0.30, 0.08, 0.30, 0.85, 0.85, 0.85)
    # Badan kerucut (pakai tiang silinder meruncing)
    glColor3f(0.95, 0.45, 0.05)
    q = gluNewQuadric()
    glPushMatrix(); glTranslatef(0, 0.08, 0); glRotatef(-90, 1, 0, 0)
    gluCylinder(q, 0.13, 0.0, 0.55, 8, 1)
    gluDeleteQuadric(q); glPopMatrix()
    # Garis putih
    box(0, 0.30, 0, 0.15, 0.05, 0.15, 0.95, 0.95, 0.95)
    glPopMatrix()

def draw_pagar_konstruksi(cx, cz, panjang=2.0, rot_y=0):
    """Pagar/barrier konstruksi oranye-putih."""
    glPushMatrix(); glTranslatef(cx, 0, cz); glRotatef(rot_y, 0, 1, 0)
    half = panjang / 2
    # Tiang kiri & kanan
    tiang_vertikal(-half, 0, 0, 0.06, 1.0, 6, 0.25, 0.25, 0.25)
    tiang_vertikal( half, 0, 0, 0.06, 1.0, 6, 0.25, 0.25, 0.25)
    # Panel oranye-putih berselang
    for j in range(4):
        xc = -half + (j + 0.5) * (panjang / 4)
        c = (0.95, 0.45, 0.05) if j % 2 == 0 else (0.92, 0.92, 0.92)
        box(xc, 0.55, 0, panjang/4 - 0.02, 0.35, 0.10, *c)
    # Rel atas
    box(0, 0.92, 0, panjang, 0.07, 0.10, 0.30, 0.30, 0.30)
    glPopMatrix()

def draw_tanda_konstruksi(cx, cz):
    """Papan tanda 'UNDER CONSTRUCTION'."""
    tiang_vertikal(cx, 0, cz, 0.05, 1.8, 6, 0.55, 0.35, 0.10)
    # Papan kuning
    box(cx, 1.95, cz, 1.20, 0.60, 0.08, 0.95, 0.80, 0.05)
    box(cx, 1.95, cz, 1.30, 0.70, 0.06, 0.25, 0.18, 0.04)
    # Strip diagonal hitam
    for k in range(3):
        ox = -0.35 + k * 0.35
        box(cx + ox, 1.95, cz - 0.02, 0.12, 0.55, 0.05, 0.10, 0.10, 0.10)

def draw_excavator_sederhana(cx, cz):
    """Alat berat / excavator mini."""
    glPushMatrix(); glTranslatef(cx, 0, cz)
    # Badan bawah (track)
    box(0, 0.18, 0,  2.2, 0.36, 1.0, 0.20, 0.18, 0.16)
    # Roda track kiri kanan
    for oz in (-0.55, 0.55):
        silinder(-0.9, 0.18, oz, 0.18, 1.8, 8, 0.15, 0.15, 0.15)
        silinder( 0.9, 0.18, oz, 0.18, 0.0, 8, 0.15, 0.15, 0.15)
    # Kabin
    box(0, 0.72, 0, 1.4, 0.65, 0.9, 0.88, 0.65, 0.10)
    # Kaca kabin
    box(0.60, 0.80, 0, 0.08, 0.40, 0.70, 0.60, 0.82, 0.92)
    # Lengan boom
    glPushMatrix(); glTranslatef(0.55, 1.05, 0); glRotatef(-40, 0, 0, 1)
    box(0.50, 0.05, 0, 1.0, 0.14, 0.18, 0.55, 0.40, 0.10)
    glTranslatef(1.0, 0, 0); glRotatef(50, 0, 0, 1)
    box(0.35, 0.05, 0, 0.70, 0.12, 0.16, 0.50, 0.36, 0.08)
    glTranslatef(0.70, 0, 0)
    # Bucket
    box(0.12, -0.15, 0, 0.35, 0.30, 0.28, 0.30, 0.25, 0.08)
    glPopMatrix()
    glPopMatrix()

def draw_jalan_utara_konstruksi_dan_demo():
    """
    Jalan cabang utara (z=-28):
    - Sisi luar (z=-31): zona konstruksi (cone, pagar, excavator, tanda)
    - Sisi dalam (z=-25): zona demo rakyat (orang demo, spanduk, poster)
    Area persimpangan (abs(x) < 9) tetap kosong.
    """
    CLEAR_X = 9.0

    # ══ SISI LUAR z≈-31: KONSTRUKSI ══════════════════════════════════
    # Deretan cone lalu lintas
    for xc in range(-28, 29, 3):
        if abs(xc) < CLEAR_X: continue
        draw_cone_lalu_lintas(xc, -31.5)

    # Pagar konstruksi berjejer
    for xc in [-25, -18, -11, 11, 18, 25]:
        draw_pagar_konstruksi(xc, -32.0, panjang=5.5, rot_y=0)

    # Tanda konstruksi
    for xc in [-22, -14, 13, 21]:
        draw_tanda_konstruksi(xc, -33.0)

    # Excavator di dua titik
    draw_excavator_sederhana(-20, -33.5)
    draw_excavator_sederhana( 18, -33.5)

    # Material konstruksi: tumpukan pasir/batu (box)
    for xc in [-16, -10, 14, 22]:
        if abs(xc) < CLEAR_X: continue
        box(xc, 0.20, -33.0, 1.8, 0.40, 1.2, 0.72, 0.60, 0.35)  # pasir
        box(xc + 0.5, 0.10, -32.2, 0.8, 0.20, 0.8, 0.45, 0.42, 0.40)  # kerikil

    # ══ SISI DALAM z≈-25: KONSTRUKSI (blokir kendaraan masuk) ════════
    # Pagar konstruksi rapat menutup akses
    for xc in [-26, -20, -14, 11, 17, 23]:
        draw_pagar_konstruksi(xc, -25.0, panjang=5.5, rot_y=0)

    # Cone rapat di garis masuk jalan
    for xc in range(-28, 29, 2):
        if abs(xc) < CLEAR_X: continue
        draw_cone_lalu_lintas(xc, -25.8)

    # Tanda konstruksi tambahan
    for xc in [-24, -15, 12, 22]:
        draw_tanda_konstruksi(xc, -24.2)

    # Tumpukan material (pasir, kerikil, pipa)
    for xc in [-22, -16, 13, 20]:
        if abs(xc) < CLEAR_X: continue
        box(xc,       0.22, -24.5, 2.0, 0.45, 1.0, 0.72, 0.60, 0.35)  # pasir
        box(xc + 0.6, 0.12, -25.2, 1.0, 0.24, 0.9, 0.45, 0.42, 0.40)  # kerikil
        # Tumpukan pipa (silinder horizontal)
        for k in range(3):
            glPushMatrix()
            glTranslatef(xc - 0.5, 0.12 + k * 0.22, -23.8)
            glRotatef(90, 0, 1, 0)
            q = gluNewQuadric()
            glColor3f(0.55, 0.55, 0.58)
            gluCylinder(q, 0.10, 0.10, 1.2, 8, 1)
            gluDisk(q, 0, 0.10, 8, 1)
            glTranslatef(0, 0, 1.2); gluDisk(q, 0, 0.10, 8, 1)
            gluDeleteQuadric(q)
            glPopMatrix()

    # ══ UJUNG BARAT (x negatif): blokir total akses masuk ════════════
    # Pagar tegak lurus menutup ujung barat jalan cabang utara
    for zc in [-32.5, -30.5, -28.0, -25.5]:
        draw_pagar_konstruksi(-29.5, zc, panjang=3.5, rot_y=90)

    # Cone di garis batas ujung barat
    for zc_cone in [-32.0, -30.8, -29.6, -28.4, -27.2, -26.0, -24.8]:
        draw_cone_lalu_lintas(-28.8, zc_cone)

    # Tanda konstruksi di ujung
    draw_tanda_konstruksi(-29.0, -31.0)
    draw_tanda_konstruksi(-29.0, -25.5)

    # Excavator di pojok barat
    draw_excavator_sederhana(-27.5, -29.5)


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
    
    # ── Sisi kiri jalan ──
    draw_rumah_indo(-10, -20, 90, (0.90, 0.85, 0.75))
    draw_rumah_indo(-10, -12, 90, (0.80, 0.70, 0.60))
    draw_rumah_indo(-10,  -5, 90, (0.75, 0.80, 0.70))
    draw_rumah_indo(-10,   6, 90, (0.88, 0.78, 0.65))
    draw_rumah_indo(-10,  15, 90, (0.70, 0.75, 0.80))

    # ── Sisi kanan jalan ──
    draw_rumah_indo(10, -20, -90, (0.82, 0.76, 0.65))
    draw_rumah_indo(10,  -8, -90, (0.78, 0.82, 0.72))
    draw_rumah_indo(10,   3.8, -90, (0.88, 0.80, 0.68))
    draw_rumah_indo(10,  16, -90, (0.72, 0.78, 0.85))
    draw_rumah_indo(10,  20.5, -90, (0.80, 0.70, 0.72))

def draw_zebra_dan_trotoar():
    """Zebra crossing simetris, stop line, dan trotoar di pinggir jalan raya."""

    # ── Trotoar kanan & kiri jalan raya utama ───────────────────────────
    trot = (0.68, 0.66, 0.63)
    kerb = (0.45, 0.43, 0.41)
    # Trotoar (lebar 1.5, sepanjang jalan, y sedikit lebih tinggi dari aspal)
    # Segmen tengah (asli)
    box( 5.25, 0.12,  0, 1.5, 0.24, 44, *trot)
    box(-5.25, 0.12,  0, 1.5, 0.24, 44, *trot)
    # Ujung utara (z=-34 s/d -22)
    box( 5.25, 0.12, -28, 1.5, 0.24, 14, *trot)
    box(-5.25, 0.12, -28, 1.5, 0.24, 14, *trot)
    # Ujung selatan (z=+22 s/d +34)
    box( 5.25, 0.12,  28, 1.5, 0.24, 14, *trot)
    box(-5.25, 0.12,  28, 1.5, 0.24, 14, *trot)
    # Kanstin / kerb pemisah jalan-trotoar
    box( 4.05, 0.06,  0, 0.12, 0.14, 44, *kerb)
    box(-4.05, 0.06,  0, 0.12, 0.14, 44, *kerb)
    box( 4.05, 0.06, -28, 0.12, 0.14, 14, *kerb)
    box(-4.05, 0.06, -28, 0.12, 0.14, 14, *kerb)
    box( 4.05, 0.06,  28, 0.12, 0.14, 14, *kerb)
    box(-4.05, 0.06,  28, 0.12, 0.14, 14, *kerb)
    # Garis nat ubin trotoar (tiap 1.5 unit)
    for sz in range(-29, 30, 2):
        box( 5.25, 0.245, sz, 1.5, 0.005, 0.06, 0.55, 0.53, 0.51)
        box(-5.25, 0.245, sz, 1.5, 0.005, 0.06, 0.55, 0.53, 0.51)

    # ── Garis berhenti (stop line) sebelum palang ────────────────────────
    box(0, 0.055, -4.5, 8.0, 0.02, 0.20, 0.92, 0.92, 0.92)
    box(0, 0.055,  4.5, 8.0, 0.02, 0.20, 0.92, 0.92, 0.92)

    # ── Zebra crossing simetris selebar aspal saja (x: -4..+4) ──────────
    lebar = 0.50
    celah = 0.28
    n     = 9
    total = n * lebar + (n - 1) * celah
    for zc in (7.0, -7.0):
        x0 = -total / 2
        for i in range(n):
            xs = x0 + i * (lebar + celah) + lebar / 2
            box(xs, 0.055, zc, lebar, 0.02, 4.0, 0.93, 0.93, 0.93)
            

def draw_portal(sudut, merah):
    draw_satu_palang(-4.5,-2.5, sudut, arah=+1)
    draw_satu_palang( 4.5, 2.5, sudut, arah=-1)
    draw_lampu( 4.5,-3.5, merah, arah_z=-1)
    draw_lampu(-4.5, 3.5, merah, arah_z=+1)
    draw_pos_jaga()

def draw_stasiun():
    """
    Stasiun kecil bergaya Indonesia.
    Diposisikan di x=-45 (jauh dari sweep kereta yang max s.d. x=-30).
    Bangunan punya depth Z yang proper sehingga tidak flat.
    """
    sx = -45.0   # geser lebih jauh dari rel (kereta max sweep x=-30)
    sz =  0.0    # sejajar sumbu rel
 
    # ── Pondasi / platform peron ──────────────────────────────────────────
    # Peron memanjang di sumbu X, lebar ke arah Z (sisi penumpang)
    # DIPERBAIKI: Y turun dari 0.20 → 0.05 dan 0.08 → 0.02 agar tidak nabrak rel
    box(sx, 0.05, sz,       14.0, 0.10, 5.0,  0.62, 0.58, 0.54)   # lantai peron utama
    box(sx, 0.02, sz - 4.0, 14.0, 0.04, 2.0,  0.50, 0.47, 0.44)   # bahu/tepi peron
 
    # ── Bangunan utama stasiun (sekarang punya depth Z = 4.0) ─────────────
    DEPTH_Z = 4.0     # kedalaman bangunan (sumbu Z)
    bz = sz + 3.5     # pusat bangunan di sisi belakang peron (z positif)
 
    # STRUKTUR UTAMA: Body bangunan yang lebih besar & kokoh
    # Dinding depan (menghadap peron / rel) - berwarna krem cerah khas stasiun
    box(sx + 1.5, 1.35, bz,            8.0, 3.00, 0.30, 0.92, 0.88, 0.82)
    # Dinding belakang
    box(sx + 1.5, 1.35, bz + DEPTH_Z,  8.0, 3.00, 0.30, 0.85, 0.81, 0.74)
    # Dinding samping kiri
    box(sx - 2.5, 1.35, bz + DEPTH_Z/2, 0.30, 3.00, DEPTH_Z, 0.88, 0.84, 0.76)
    # Dinding samping kanan
    box(sx + 5.5, 1.35, bz + DEPTH_Z/2, 0.30, 3.00, DEPTH_Z, 0.88, 0.84, 0.76)
    # Plafon / langit-langit
    box(sx + 1.5, 3.00, bz + DEPTH_Z/2, 8.0, 0.12, DEPTH_Z, 0.78, 0.75, 0.68)
    
    # SAYAP/WINGS - Area tunggu dan tiket lebih besar
    # Sayap kiri (ruang tunggu) 
    box(sx - 3.2, 1.20, bz + DEPTH_Z/2 - 0.8, 3.5, 2.50, DEPTH_Z - 0.2, 0.88, 0.84, 0.76)
    # Sayap kanan (kantor/tiket)
    box(sx + 6.2, 1.20, bz + DEPTH_Z/2 - 0.8, 3.0, 2.50, DEPTH_Z - 0.2, 0.88, 0.84, 0.76)
    
    # KOLOM/PILAR DEPAN - untuk sokongan struktur & estetika
    for col_x in [sx - 1.0, sx + 1.5, sx + 4.0, sx + 6.5]:
        box(col_x, 0.15, bz - 0.05, 0.25, 3.20, 0.25, 0.80, 0.76, 0.68)
    
    # ── PORTICO / SERAMBI DEPAN (entrance shelter) ────────────────────────
    # Platform serambi (raised deck)
    box(sx + 1.5, 0.12, bz - 0.50, 5.0, 0.24, 1.50, 0.68, 0.64, 0.58)
    
    # Atap serambi (menjulur ke depan)
    draw_prisma_atap(sx + 1.5, 3.20, bz - 0.50, 5.5, 1.50, 1.60, 0.60, 0.20, 0.08)
    
    # Pilar serambi (4 tiang)
    for serambi_x in [sx - 1.0, sx + 0.5, sx + 3.0, sx + 4.5]:
        tiang_vertikal(serambi_x, 0.12, bz - 0.50, 0.16, 3.10, 8, 0.72, 0.68, 0.60)
        box(serambi_x, 0.15, bz - 0.50, 0.28, 0.30, 0.28, 0.58, 0.53, 0.46)  # base
 
    # ── Atap utama (genteng coklat merah) — Z ikut membesar ───────────────
    # Atap utama yang lebih kokoh
    draw_prisma_atap(sx + 1.5, 3.05, bz + DEPTH_Z/2,  8.5, 1.40, DEPTH_Z + 1.0, 0.62, 0.22, 0.10)
    
    # Atap sayap kiri
    draw_prisma_atap(sx - 3.2, 2.55, bz + DEPTH_Z/2 - 0.8, 4.0, 1.00, DEPTH_Z + 0.3, 0.60, 0.20, 0.08)
    
    # Atap sayap kanan
    draw_prisma_atap(sx + 6.2, 2.55, bz + DEPTH_Z/2 - 0.8, 3.5, 1.00, DEPTH_Z + 0.3, 0.60, 0.20, 0.08)
    
    # OVERHANGS / TERITISAN - untuk perlindungan depan (khas stasiun)
    box(sx + 1.5, 3.10, bz - 0.35, 8.5, 0.08, 0.60, 0.55, 0.18, 0.08)   # teritisan depan
    box(sx + 1.5, 3.10, bz + DEPTH_Z + 0.35, 8.5, 0.08, 0.60, 0.55, 0.18, 0.08)   # teritisan belakang
    
    # ── SKYLIGHT & VENTILASI ATAP ──────────────────────────────────────────
    # Skylight/cupola (untuk cahaya & ventilasi)
    box(sx - 1.0, 3.15, bz + DEPTH_Z/2 - 1.0, 1.20, 0.20, 1.20, 0.50, 0.50, 0.52)   # skylight kiri
    box(sx + 4.0, 3.15, bz + DEPTH_Z/2 + 1.0, 1.20, 0.20, 1.20, 0.50, 0.50, 0.52)   # skylight kanan
    
    # Ventilasi samping atap (untuk aerasi)
    for vent_x in [sx - 2.5, sx + 5.5]:
        silinder(vent_x, 3.20, bz + DEPTH_Z/2, 0.15, 0.20, 8, 0.55, 0.55, 0.55)
        box(vent_x, 3.25, bz + DEPTH_Z/2, 0.35, 0.10, 0.35, 0.40, 0.40, 0.42)
 
    # ── Jendela & pintu bangunan ───────────────────────────────────────────
    # PINTU UTAMA - double door besar (main entrance)
    box(sx + 1.5, 1.00, bz - 0.03,  1.20, 2.00, 0.08, 0.45, 0.28, 0.12)   # kusen pintu
    box(sx + 1.5, 1.05, bz - 0.05,  0.95, 1.80, 0.05, 0.70, 0.85, 0.95)   # kaca kiri
    box(sx + 2.0, 1.05, bz - 0.05,  0.95, 1.80, 0.05, 0.70, 0.85, 0.95)   # kaca kanan
    
    # JENDELA DERET DEPAN - untuk kasir & info
    for win_x in [-1.0, 1.5, 4.0]:
        box(sx + win_x, 1.30, bz - 0.03,  0.95, 0.90, 0.08, 0.50, 0.32, 0.15)   # kusen
        box(sx + win_x, 1.35, bz - 0.05,  0.75, 0.70, 0.05, 0.68, 0.88, 0.95)   # kaca
    
    # JENDELA SAYAP KIRI (ruang tunggu)
    for lwin_x in [-4.2, -2.7]:
        box(sx + lwin_x, 1.20, bz + DEPTH_Z/2 - 0.05, 0.90, 0.85, 0.10, 0.68, 0.88, 0.95)
    
    # JENDELA SAYAP KANAN (tiket/kantor)
    for rwin_x in [5.2, 6.8]:
        box(sx + rwin_x, 1.20, bz + DEPTH_Z/2 - 0.05, 0.90, 0.85, 0.10, 0.68, 0.88, 0.95)
    
    # JENDELA BELAKANG (ventilasi)
    box(sx + 1.5, 1.30, bz + DEPTH_Z + 0.03, 1.50, 0.80, 0.08, 0.68, 0.88, 0.95)
 
    # ── Papan nama stasiun ─────────────────────────────────────────────────
    # Papan utama KAI (kuning gold khas Indonesia)
    box(sx + 1.5, 2.65, bz - 0.08,  4.00, 0.50, 0.16, 0.95, 0.82, 0.15)   # papan kuning
    box(sx + 1.5, 2.65, bz - 0.10,  4.20, 0.60, 0.12, 0.35, 0.28, 0.12)   # frame/bingkai
    
    # LOGO/EMBLEM belakang pintu
    bola(sx + 1.5, 2.20, bz - 0.06, 0.20, cr=0.95, cg=0.82, cb=0.15)   # logo melingkar
    
    # LAMPU PAPAN (indikator)
    bola(sx - 0.5, 2.65, bz - 0.10, 0.08, cr=1.0, cg=0.98, cb=0.72)   # lampu kiri
    bola(sx + 3.5, 2.65, bz - 0.10, 0.08, cr=1.0, cg=0.98, cb=0.72)   # lampu kanan
 
    # ── Kanopi peron (atap peneduh, memanjang di atas peron) ──────────────
    # DIPERBAIKI: Naikkan kanopi dari Y=2.70 → 3.20 dan tiang lebih panjang
    box(sx, 3.20, sz - 0.5,  14.0, 0.10, 3.2, 0.50, 0.50, 0.52)   # atap kanopi
    box(sx, 3.05, sz - 0.5,  13.6, 0.06, 3.0, 0.38, 0.38, 0.40)   # rangka bawah
    # Tiang-tiang kanopi
    for tx_off in [-5.0, -2.0, 1.0, 4.0]:
        tiang_vertikal(sx + tx_off, 0.40, sz - 0.5, 0.09, 2.80, 8, 0.30, 0.30, 0.32)
        box(sx + tx_off, 0.24, sz - 0.5, 0.30, 0.08, 0.30, 0.42, 0.40, 0.38)   # plat kaki
 
    # ── Bangku tunggu di peron ─────────────────────────────────────────────
    for bx_off in [-4.0, -0.5, 3.0]:
        bx = sx + bx_off
        box(bx, 0.95, sz - 0.30, 1.60, 0.08, 0.08, 0.38, 0.22, 0.08)  # sandaran
        box(bx, 0.68, sz - 0.30, 1.60, 0.08, 0.38, 0.35, 0.20, 0.08)  # dudukan
        box(bx - 0.68, 0.44, sz - 0.30, 0.08, 0.44, 0.38, 0.28, 0.16, 0.06)  # kaki kiri
        box(bx + 0.68, 0.44, sz - 0.30, 0.08, 0.44, 0.38, 0.28, 0.16, 0.06)  # kaki kanan
 
    # ── Lampu peron ───────────────────────────────────────────────────────
    for lx_off in [-4.5, 0.0, 4.5]:
        lx = sx + lx_off
        tiang_vertikal(lx, 0.40, sz - 1.20, 0.06, 2.35, 8, 0.20, 0.20, 0.22)
        silinder(lx - 0.12, 2.72, sz - 1.20, 0.08, 0.24, 8, 0.12, 0.12, 0.12)
        bola(lx + 0.12, 2.78, sz - 1.20, 0.12, cr=1.0, cg=0.98, cb=0.72)
 
    # ── Tiang sinyal sederhana ────────────────────────────────────────────
    tiang_vertikal(sx + 6.2, 0.40, sz - 0.80, 0.08, 3.30, 8, 0.20, 0.20, 0.22)
    box(sx + 6.2, 3.55, sz - 0.80, 0.50, 0.50, 0.08, 0.90, 0.75, 0.05)
    box(sx + 6.2, 3.85, sz - 0.80, 0.50, 0.08, 0.08, 0.85, 0.10, 0.10)
    bola(sx + 6.2, 3.70, sz - 0.75, 0.10, cr=0.95, cg=0.08, cb=0.08)
 
    # ── Pilar dekoratif sudut bangunan ────────────────────────────────────
    # Pilar utama di sudut (untuk arsitektur yang lebih kokoh)
    for px_off in [-2.5, 5.5]:
        # Pilar utama
        tiang_vertikal(sx + px_off, 0.00, bz + DEPTH_Z/2, 0.20, 3.00, 8, 0.75, 0.70, 0.62)
        # Base/alas pilar
        box(sx + px_off, 0.15, bz + DEPTH_Z/2, 0.35, 0.30, 0.35, 0.65, 0.60, 0.52)
        # Capital (puncak) pilar
        box(sx + px_off, 3.02, bz + DEPTH_Z/2, 0.40, 0.15, 0.40, 0.70, 0.65, 0.58)
 
    # ── Tangga turun dari peron ke jalan ──────────────────────────────────
    for step in range(4):
        box(sx - 5.5, step * 0.09 + 0.05, sz - 1.8 - step * 0.25,
            1.20, 0.10, 0.52,
            0.55, 0.52, 0.48)
 
    # ── Pagar pengaman tepi peron (sisi rel) ─────────────────────────────
    for fx in range(-6, 7):
        tiang_vertikal(sx + fx * 1.1, 0.40, sz - 1.90, 0.04, 0.55, 6, 0.45, 0.42, 0.40)
    box(sx, 0.94, sz - 1.90, 13.0, 0.06, 0.06, 0.45, 0.42, 0.40)
    box(sx, 0.70, sz - 1.90, 13.0, 0.04, 0.04, 0.45, 0.42, 0.40)
 
    # ── Pot bunga / tanaman hias di depan stasiun ─────────────────────────
    for px_off, pz_off in [(-4.2, bz - 0.20), (6.8, bz - 0.20)]:
        silinder(sx + px_off, 0.40, pz_off, 0.22, 0.28, 8, 0.55, 0.35, 0.18)
        silinder(sx + px_off, 0.68, pz_off, 0.18, 0.20, 8, 0.18, 0.50, 0.15)
        bola(sx + px_off, 0.92, pz_off, 0.22, cr=0.18, cg=0.52, cb=0.15)
 
    # ── Area parkir / halaman stasiun ─────────────────────────────────────
    box(sx, 0.03, bz + DEPTH_Z + 3.0, 16.0, 0.06, 4.0, 0.40, 0.38, 0.36)   # aspal parkir
    # Marka parkir
    for px_off in [-5.5, -2.0, 1.5, 5.0]:
        box(sx + px_off, 0.07, bz + DEPTH_Z + 3.0, 0.10, 0.01, 3.5, 0.75, 0.75, 0.75)
    
    # ── PAPAN INFORMASI BESAR (di area parkir depan) ──────────────────────
    # Tiang penopang papan besar
    tiang_vertikal(sx - 6.0, 0.20, bz + DEPTH_Z + 1.5, 0.16, 2.80, 8, 0.55, 0.50, 0.45)
    tiang_vertikal(sx + 8.0, 0.20, bz + DEPTH_Z + 1.5, 0.16, 2.80, 8, 0.55, 0.50, 0.45)
    
    # Papan informasi utama (kaya papan jalanan)
    box(sx + 1.0, 2.50, bz + DEPTH_Z + 1.5, 14.0, 0.50, 0.12, 0.92, 0.88, 0.15)   # papan info kuning
    box(sx + 1.0, 2.50, bz + DEPTH_Z + 1.52, 14.2, 0.55, 0.08, 0.30, 0.25, 0.10)   # frame/bingkai hitam
    
    # Lampu penerang papan (di sudut)
    silinder(sx - 6.0, 2.85, bz + DEPTH_Z + 1.5, 0.10, 0.15, 8, 0.15, 0.15, 0.15)
    bola(sx - 6.0, 3.05, bz + DEPTH_Z + 1.5, 0.12, cr=1.0, cg=0.98, cb=0.72)
    silinder(sx + 8.0, 2.85, bz + DEPTH_Z + 1.5, 0.10, 0.15, 8, 0.15, 0.15, 0.15)
    bola(sx + 8.0, 3.05, bz + DEPTH_Z + 1.5, 0.12, cr=1.0, cg=0.98, cb=0.72)

# ═══════════════════════════════════════════════
#  KERETA
# ═══════════════════════════════════════════════
def draw_roda_kereta(cx, cy, cz):
    # Axle: batang horizontal kiri-kanan (sumbu Z), tidak perlu rotate
    glPushMatrix()
    glTranslatef(cx, cy, cz - 0.7)
    glColor3f(0.3, 0.3, 0.3)
    q = gluNewQuadric()
    gluCylinder(q, 0.08, 0.08, 1.4, 8, 1)
    gluDeleteQuadric(q)
    glPopMatrix()

    # Roda kiri dan kanan — tegak di bidang XY
    for oz in [-0.7, 0.7]:
        glPushMatrix()
        glTranslatef(cx, cy, cz + oz - 0.06)
        # TIDAK ada glRotatef — gluCylinder ke +Z = ketebalan ban (tipis, arah Z)
        # Lingkaran roda = disk di bidang XY → sudah benar tanpa rotate
        glColor3f(0.15, 0.15, 0.15)
        q = gluNewQuadric()
        gluCylinder(q, 0.35, 0.35, 0.12, 14, 1)  # ban tipis, tegak di XY
        gluDisk(q, 0, 0.35, 14, 1)                # sisi dalam
        glTranslatef(0, 0, 0.12)
        gluDisk(q, 0, 0.35, 14, 1)                # sisi luar
        gluDeleteQuadric(q)
        glPopMatrix()

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
    glPushMatrix()
    glTranslatef(0, 0.35, 0)   # angkat seluruh kereta agar roda di atas rel
    glPushMatrix(); glTranslatef(px,0,0); glRotatef(180,0,1,0)
    draw_lokomotif(0); glPopMatrix()
    for i in range(4):
        draw_gerbong(px+5.8+i*5.6)
    glPopMatrix()

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
    box(0,0.32, 0,    1.0,0.52,2.2,  r*0.85,g*0.85,b*0.85)  # bodi bawah
    box(0,0.82, 0.35, 0.9,0.45,1.2,  r,g,b)                  # kabin (geser ke belakang)
    box(0,0.85,-0.25, 0.85,0.35,0.04,0.6,0.82,0.92)          # kaca depan (muka kabin)
    box(0,0.85, 0.95, 0.85,0.30,0.04,0.6,0.82,0.92)          # kaca belakang
    box( 0.38,0.38,-1.11,0.18,0.12,0.04,1.0,1.0,0.8)         # lampu depan kanan
    box(-0.38,0.38,-1.11,0.18,0.12,0.04,1.0,1.0,0.8)         # lampu depan kiri
    draw_roda_k( 0.52,0.25, 0.75); draw_roda_k(-0.52,0.25, 0.75)
    draw_roda_k( 0.52,0.25,-0.75); draw_roda_k(-0.52,0.25,-0.75)
    glPopMatrix()

def draw_motor_obj(x, z, wi=0):
    r,g,b = WARNA[wi % len(WARNA)]
    glPushMatrix(); glTranslatef(x,0,z)
    box(0,0.42,0,   0.40,0.28,1.10, r,g,b)
    box(0,0.65,-0.1, 0.38,0.18,0.55, r*0.9,g*0.9,b*0.9)
    box(0,0.78,-0.48,0.68,0.07,0.07, 0.25,0.25,0.25)
    box(0,0.55,-0.58,0.30,0.22,0.12, 0.15,0.15,0.15)
    bola(0,0.55,-0.65,0.08, cr=1.0,cg=1.0,cb=0.7)
    box(0.22,0.28, 0.30,0.06,0.08,0.70, 0.50,0.50,0.50)
    box(0,0.28,0,   0.34,0.22,0.55, 0.20,0.20,0.22)
    box(0,0.62, 0.15,0.38,0.10,0.52, 0.12,0.10,0.10)
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
    """Satu unit kendaraan (mobil / motor). Bergerak lurus tanpa belok."""

    def __init__(self, z, x, tipe, warna):
        self.z        = float(z)
        self.x        = float(x)
        self.tipe     = tipe
        self.warna    = warna
        self.arah     = 1 if x < 0 else -1
        self.speed    = 3.8 if tipe == 'motor' else 3.2
        self.berhenti = False

    def update(self, dt, palang_tutup, depan_z=None, pejalan_list=None):
        jarak_aman   = 3.5 if self.tipe == 'motor' else 4.5
        panjang_body = 1.2 if self.tipe == 'motor' else 2.2

        ada_penyebrang = False
        if pejalan_list:
            for pk in pejalan_list:
                if not pk.aktif:
                    continue
                if pk.x < -3.5:
                    continue
                zc = pk.zc
                if self.arah == 1:
                    zebra_di_depan = (self.z < zc + 2.5) and (self.z > zc - 14.0)
                else:
                    zebra_di_depan = (self.z > zc - 2.5) and (self.z < zc + 14.0)
                if zebra_di_depan:
                    ada_penyebrang = True
                    break

        harus_berhenti = palang_tutup or ada_penyebrang

        STOP_LINE = 9.5
        batas_berhenti = -STOP_LINE * self.arah
        sudah_lewat = (
            (self.arah ==  1 and self.z >= batas_berhenti) or
            (self.arah == -1 and self.z <= batas_berhenti)
        )

        if harus_berhenti and not sudah_lewat:
            default_stop = batas_berhenti - self.arah * panjang_body * 0.5
            if depan_z is not None:
                posisi_berhenti = depan_z - self.arah * jarak_aman
                if self.arah == 1:
                    posisi_berhenti = min(posisi_berhenti, default_stop)
                else:
                    posisi_berhenti = max(posisi_berhenti, default_stop)
            else:
                posisi_berhenti = default_stop

            selisih = (posisi_berhenti - self.z) * self.arah
            if selisih > 0.05:
                self.z += self.arah * self.speed * dt
                if (self.arah == 1  and self.z > posisi_berhenti) or \
                   (self.arah == -1 and self.z < posisi_berhenti):
                    self.z = posisi_berhenti
            self.berhenti = True
            return

        self.berhenti = False

        if depan_z is not None:
            jarak = (depan_z - self.z) * self.arah
            if jarak < jarak_aman:
                return

        # Gerak maju lurus
        self.z += self.arah * self.speed * dt
        if self.z >  34: self.z = -34
        if self.z < -34: self.z =  34

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        glRotatef(180.0 if self.arah == 1 else 0.0, 0, 1, 0)
        if self.tipe == 'mobil':
            draw_mobil(0, 0, self.warna)
        else:
            draw_motor_obj(0, 0, self.warna)
        glPopMatrix()

    def world_pos(self):
        return (self.x, 0.0, self.z)

    def heading_deg(self):
        return 180.0 if self.arah == 1 else 0.0


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
    """Jalan cabang sekarang Car Free Day – tidak ada kendaraan."""
    return []

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

        # ── FREE CAM state ────────────────────────────────
        self._free_pos   = [0.0, 5.0, 20.0]
        self._free_yaw   = 180.0
        self._free_pitch = -10.0
        self._free_speed = 8.0
        self._free_sens  = 0.25
        self._keys_held  = set()

    # ══════════════════════════════════════════
    #  INPUT CALLBACKS
    # ══════════════════════════════════════════
    def on_key(self, window, key, sc, act, mod, kendaraan_list=None):
        if kendaraan_list is None:
            kendaraan_list = []
        if act == glfw.PRESS:
            self._keys_held.add(key)
        elif act == glfw.RELEASE:
            self._keys_held.discard(key)
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
            elif key == glfw.KEY_4:
                self.mode = CAM_FREE
                print("[CAM] Mode 4 – FREE CAM")
                print("       W/S=Maju/Mundur | A/D=Kiri/Kanan | Q/E=Turun/Naik")
                print("       SHIFT=Cepat | Mouse drag kiri=Putar pandang | Scroll=Zoom")
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
        if button == glfw.MOUSE_BUTTON_LEFT or button == glfw.MOUSE_BUTTON_MIDDLE:
            self._mdown = (act == glfw.PRESS)
            if self._mdown:
                self._mx, self._my = glfw.get_cursor_pos(window)

    def on_cursor(self, window, xpos, ypos):
        dx = xpos - self._mx
        dy = ypos - self._my
        self._mx, self._my = xpos, ypos
        if self.mode == CAM_OVERVIEW and self._mdown:
            self.yaw   += dx * 0.4
            self.pitch  = max(5.0, min(85.0, self.pitch + dy * 0.3))
        elif self.mode == CAM_FREE and self._mdown:
            self._free_yaw   += dx * self._free_sens
            self._free_pitch -= dy * self._free_sens
            self._free_pitch  = max(-89.0, min(89.0, self._free_pitch))

    def on_scroll(self, window, xoff, yoff):
        if self.mode == CAM_OVERVIEW:
            self.dist = max(5.0, min(50.0, self.dist - yoff * 1.0))
        elif self.mode == CAM_FREE:
            fwd = self._free_forward_vec()
            for i in range(3):
                self._free_pos[i] += fwd[i] * yoff * 3.0

    # ══════════════════════════════════════════
    #  KALKULASI TARGET KAMERA
    # ══════════════════════════════════════════

    def _free_forward_vec(self):
        yr = math.radians(self._free_yaw)
        pr = math.radians(self._free_pitch)
        return [
            math.cos(pr) * math.sin(yr),
            math.sin(pr),
            math.cos(pr) * math.cos(yr),
        ]

    def _free_right_vec(self):
        yr = math.radians(self._free_yaw)
        return [-math.cos(yr), 0.0, math.sin(yr)]

    def update_free_cam(self, dt, window=None):
        if self.mode != CAM_FREE:
            return
        shift = (glfw.KEY_LEFT_SHIFT  in self._keys_held or
                 glfw.KEY_RIGHT_SHIFT in self._keys_held)
        spd   = self._free_speed * (3.0 if shift else 1.0)
        fwd   = self._free_forward_vec()
        right = self._free_right_vec()
        move  = [0.0, 0.0, 0.0]
        if glfw.KEY_W in self._keys_held:
            for i in range(3): move[i] += fwd[i]
        if glfw.KEY_S in self._keys_held:
            for i in range(3): move[i] -= fwd[i]
        if glfw.KEY_D in self._keys_held:
            for i in range(3): move[i] += right[i]
        if glfw.KEY_A in self._keys_held:
            for i in range(3): move[i] -= right[i]
        if glfw.KEY_E in self._keys_held:
            move[1] += 1.0
        if glfw.KEY_Q in self._keys_held:
            move[1] -= 1.0
        mag = math.sqrt(sum(v * v for v in move))
        if mag > 1e-6:
            move = [v / mag for v in move]
        for i in range(3):
            self._free_pos[i] += move[i] * spd * dt

    def _target_free(self):
        fwd    = self._free_forward_vec()
        eye    = list(self._free_pos)
        center = [eye[i] + fwd[i] for i in range(3)]
        return eye, center, [0.0, 1.0, 0.0]

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
        elif self.mode == CAM_FREE:
            eye_t, cen_t, up_t = self._target_free()
            smooth = 1.0
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
               CAM_FREE:      '4-FreeCam',
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

def draw_tombol_ui(win, sim):
    """Gambar tombol pause/speed di pojok kiri bawah pakai overlay 2D."""
    w, h = glfw.get_framebuffer_size(win)

    # Simpan state OpenGL
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix(); glLoadIdentity()
    glOrtho(0, w, 0, h, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix(); glLoadIdentity()

    # ── Background panel ──
    px, py = 12, 12   # pojok kiri bawah
    bw, bh = 160, 50  # ukuran panel

    glColor4f(0, 0, 0, 0.45)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glVertex2f(px,      py)
    glVertex2f(px+bw,   py)
    glVertex2f(px+bw,   py+bh)
    glVertex2f(px,      py+bh)
    glEnd()
    glDisable(GL_BLEND)

    # ── Tombol Pause (kotak kiri) ──
    # Warna: biru kalau jalan, merah kalau pause
    if sim.paused:
        glColor3f(0.9, 0.2, 0.2)
    else:
        glColor3f(0.2, 0.55, 0.9)
    glBegin(GL_QUADS)
    glVertex2f(px+8,  py+8)
    glVertex2f(px+48, py+8)
    glVertex2f(px+48, py+42)
    glVertex2f(px+8,  py+42)
    glEnd()

    # Ikon pause (2 garis) atau play (segitiga)
    glColor3f(1, 1, 1)
    if sim.paused:
        # Segitiga play ▶
        glBegin(GL_TRIANGLES)
        glVertex2f(px+18, py+12)
        glVertex2f(px+18, py+38)
        glVertex2f(px+42, py+25)
        glEnd()
    else:
        # 2 garis pause ⏸
        glBegin(GL_QUADS)
        glVertex2f(px+16, py+12); glVertex2f(px+24, py+12)
        glVertex2f(px+24, py+38); glVertex2f(px+16, py+38)
        glVertex2f(px+30, py+12); glVertex2f(px+38, py+12)
        glVertex2f(px+38, py+38); glVertex2f(px+30, py+38)
        glEnd()

    # ── Tombol Slow ◀◀ ──
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(px+58,  py+8)
    glVertex2f(px+98,  py+8)
    glVertex2f(px+98,  py+42)
    glVertex2f(px+58,  py+42)
    glEnd()
    glColor3f(1, 1, 1)
    glBegin(GL_TRIANGLES)
    glVertex2f(px+92, py+12); glVertex2f(px+70, py+25); glVertex2f(px+92, py+38)
    glVertex2f(px+80, py+12); glVertex2f(px+62, py+25); glVertex2f(px+80, py+38)
    glEnd()

    # ── Tombol Fast ▶▶ ──
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(px+108, py+8)
    glVertex2f(px+152, py+8)
    glVertex2f(px+152, py+42)
    glVertex2f(px+108, py+42)
    glEnd()
    glColor3f(1, 1, 1)
    glBegin(GL_TRIANGLES)
    glVertex2f(px+114, py+12); glVertex2f(px+136, py+25); glVertex2f(px+114, py+38)
    glVertex2f(px+126, py+12); glVertex2f(px+148, py+25); glVertex2f(px+126, py+38)
    glEnd()

    # Restore state
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW);  glPopMatrix()
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

# ═══════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════
def main():
    if not glfw.init():
        raise RuntimeError("GLFW init gagal")

    win = glfw.create_window(1200, 700, "Simulasi Perlintasan Kereta Api 3D | Car Free Day Bazaar", None, None)
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
            elif key == glfw.KEY_S and cam.mode != CAM_FREE:
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
        adt = 0.0 if sim.paused else dt   # ← dt=0 saat pause

        sim.update(dt)  # sim.update pakai dt asli (biar tombol tetap respons)
        cam.update_free_cam(dt, win)

        for kc in kend_cabang:
            kc.update(adt)   # ← pakai adt

        boleh_nyebrang = (sim.fase == FASE_KERETA)
        for pk in pejalan:
            pk.update(adt, boleh_nyebrang)   # ← pakai adt

        jalur_kiri  = sorted([k for k in kendaraan if k.x < 0], key=lambda k:  k.z)
        jalur_kanan = sorted([k for k in kendaraan if k.x > 0], key=lambda k: -k.z)
        for jalur in (jalur_kiri, jalur_kanan):
            for i, k in enumerate(jalur):
                depan = jalur[i+1] if i < len(jalur)-1 else None
                k.update(adt, sim.palang_tutup, depan.z if depan else None, pejalan_list=pejalan)  # ← pakai adt

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

        # Buat nge draw di map
        draw_jalan()
        draw_jalan_cabang()
        draw_zebra_dan_trotoar()
        draw_rel()
        draw_terowongan()
        draw_portal(sim.palang, sim.merah)
        draw_bangunan()
        draw_stasiun()
        draw_car_free_day()
        draw_jalan_utara_konstruksi_dan_demo()

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