"""
camera.py — Modul kamera standalone untuk simulasi perlintasan kereta api.

Diintegrasikan juga ke CameraSystem di main.py.
Impor modul ini jika ingin pakai CameraSystem secara terpisah.

Perubahan utama (v3):
  • Mode CAM_DRIVER sekarang adalah POV dashcam yang benar:
    - Eye ditempatkan di dalam bodi kendaraan, di belakang kaca depan.
    - Target pandang diletakkan jauh ke depan (15 unit) di luar kendaraan.
    - Forward vector dihitung dari k.arah (+1 / -1) sehingga kamera
      selalu menghadap ke luar, bukan ke interior mobil.
    - near-clipping plane direkomendasikan 0.05 (bukan 0.1) agar
      tidak ada polygon yang terpotong saat eye dekat kaca depan.
  • Pilih kendaraan target dengan TAB/N (next) dan P (previous).
  • Smooth lebih responsif di mode driver (factor 0.20 vs 0.10).
"""

import glfw
import math
from OpenGL.GL import *
from OpenGL.GLU import *

CAM_OVERVIEW  = 1
CAM_DRIVER    = 2
CAM_TRACKSIDE = 3


def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


# ── Profil geometri kendaraan ─────────────────────────────────────────────────
# Harus sinkron dengan draw_mobil() / draw_motor_obj() di main.py.
#
# Mobil  : bodi bawah panjang Z = 2.2  → setengah = 1.1
#           kaca depan z_lokal ≈ +0.82,  atap y ≈ 1.04
# Motor  : bodi utama panjang Z = 1.1
#           setang z_lokal ≈ +0.48,  kepala pengendara y ≈ 1.32
#
# eye_z_fwd HARUS < setengah panjang bodi agar eye tidak keluar dari geometri.
# Gap antara eye dan kaca depan harus > near-plane (0.05) agar tidak di-clip.
#   Mobil : gap = 0.82 - 0.65 = 0.17  ✓
#   Motor : gap = 0.48 - 0.35 = 0.13  ✓
# ─────────────────────────────────────────────────────────────────────────────
_PROFIL = {
    'mobil': dict(
        eye_y     = 0.88,   # tinggi mata pengemudi di atas tanah
        eye_z_fwd = 0.65,   # offset ke depan dari pusat bodi (< 1.1)
        tgt_z_fwd = 15.0,   # target pandang: 15 unit di depan (world space)
        tgt_y_dip = -0.10,  # sedikit ke bawah → melihat permukaan jalan
    ),
    'motor': dict(
        eye_y     = 1.10,   # setinggi kepala pengendara motor
        eye_z_fwd = 0.35,   # mendekati setang (< 0.55)
        tgt_z_fwd = 15.0,
        tgt_y_dip = -0.08,
    ),
}


class CameraSystem:
    """
    Sistem kamera multi-mode.

    Mode:
      CAM_OVERVIEW  (1) – bird-eye view, bebas diputar & di-zoom
      CAM_DRIVER    (2) – POV dashcam dari dalam kendaraan yang dipilih
      CAM_TRACKSIDE (3) – dari pinggir rel (sudut tetap)

    Keyboard:
      1 / 2 / 3    → ganti mode
      TAB / N      → (mode driver) kendaraan berikutnya
      P            → (mode driver) kendaraan sebelumnya
      + / -        → zoom (mode overview)
      ESC          → tutup window
    Mouse:
      Drag kiri    → putar (mode overview)
      Scroll       → zoom (mode overview)
    """

    def __init__(self):
        self.mode        = CAM_OVERVIEW
        # Overview
        self.yaw         = 45.0
        self.pitch       = 35.0
        self.dist        = 25.0
        # Mouse
        self._mx         = 0.0
        self._my         = 0.0
        self._mdown      = False
        # Smooth interpolation state
        self._eye        = [0.0, 25.0, 0.0]
        self._center     = [0.0,  0.0,  0.0]
        self._up         = [0.0,  1.0,  0.0]
        self._smooth_ov  = 0.10
        self._smooth_drv = 0.20
        # Indeks kendaraan aktif (driver mode)
        self._driver_idx = 0

    # ══════════════════════════════════════════════════════════════════════════
    #  REGISTRASI CALLBACK
    # ══════════════════════════════════════════════════════════════════════════
    def register_callbacks(self, window, kendaraan_list=None):
        """
        Daftarkan semua GLFW callback ke window.
        Oper kendaraan_list agar TAB/N/P bisa berfungsi di mode driver.
        """
        kl = kendaraan_list or []
        glfw.set_key_callback(window,
            lambda w, k, sc, act, mod: self.on_key(w, k, sc, act, mod, kl))
        glfw.set_mouse_button_callback(window, self.on_mouse_button)
        glfw.set_cursor_pos_callback(window,   self.on_cursor)
        glfw.set_scroll_callback(window,       self.on_scroll)

    # ══════════════════════════════════════════════════════════════════════════
    #  INPUT HANDLERS
    # ══════════════════════════════════════════════════════════════════════════
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
                print("       TAB/N = next kendaraan  |  P = prev")
            elif key == glfw.KEY_3:
                self.mode = CAM_TRACKSIDE
                print("[CAM] Mode 3 – Trackside")
            elif key == glfw.KEY_EQUAL:
                self.dist = max(5.0, self.dist - 1.5)
            elif key == glfw.KEY_MINUS:
                self.dist = min(50.0, self.dist + 1.5)
            elif key in (glfw.KEY_TAB, glfw.KEY_N) and self.mode == CAM_DRIVER:
                self._driver_idx = (self._driver_idx + 1) % max(1, len(kendaraan_list))
                self._log_target(kendaraan_list)
            elif key == glfw.KEY_P and self.mode == CAM_DRIVER:
                self._driver_idx = (self._driver_idx - 1) % max(1, len(kendaraan_list))
                self._log_target(kendaraan_list)

    def _log_target(self, kendaraan_list):
        if not kendaraan_list:
            return
        idx  = self._driver_idx % len(kendaraan_list)
        k    = kendaraan_list[idx]
        sisi = 'kiri' if k.x < 0 else 'kanan'
        print(f"[CAM] Driver → #{idx+1}/{len(kendaraan_list)}"
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

    # ══════════════════════════════════════════════════════════════════════════
    #  KALKULASI TARGET KAMERA PER MODE
    # ══════════════════════════════════════════════════════════════════════════
    def _target_overview(self):
        pr = math.radians(self.pitch)
        yr = math.radians(self.yaw)
        cx = self.dist * math.cos(pr) * math.sin(yr)
        cy = self.dist * math.sin(pr)
        cz = self.dist * math.cos(pr) * math.cos(yr)
        return [cx, cy, cz], [0.0, 0.5, 0.0], [0.0, 1.0, 0.0]

    def _target_driver(self, kendaraan_list):
        """
        POV dashcam yang menghadap ke luar kendaraan.

        Masalah utama mode driver lama:
          • Eye diletakkan di pusat bodi (k.z) → Eye berada di DALAM geometri.
          • Target hanya 6 unit ke depan → bila kendaraan lain ada di sana,
            target bisa tersembunyi atau arah pandang tidak natural.
          • near-plane 0.1 → polygon kendaraan sendiri di-clip dengan warna aneh.

        Solusi yang diterapkan di sini:
          1. Eye digeser maju (eye_z_fwd) mendekati kaca depan, tapi masih
             di dalam bodi sehingga tidak ada polygon antara eye dan dunia luar.
          2. Target diletakkan sangat jauh (15 unit) → gluLookAt pasti mengarah
             ke luar, tidak terhalangi geometri sendiri.
          3. Forward vector = (0, 0, k.arah) karena:
               • arah +1  → kendaraan bergerak ke +Z
               • arah -1  → kendaraan bergerak ke -Z
             Rotasi kendaraan (glRotatef 180 di draw()) tidak memengaruhi
             world-space karena kita hitung langsung dari k.arah.
          4. near-plane diperkecil jadi 0.05 di main() agar tidak ada
             clipping walau eye sangat dekat kaca depan.
        """
        if not kendaraan_list:
            return self._target_overview()

        idx = self._driver_idx % len(kendaraan_list)
        k   = kendaraan_list[idx]
        cfg = _PROFIL.get(k.tipe, _PROFIL['mobil'])

        # ── Forward vector (world space) ──────────────────────────────────────
        # +1 → bergerak ke +Z → forward = +Z
        # -1 → bergerak ke -Z → forward = -Z
        fwd_z = float(k.arah)

        # ── Eye: di dalam bodi, di belakang kaca depan ────────────────────────
        # eye_z_fwd < setengah panjang bodi → eye tidak keluar dari geometri
        # gap ke kaca depan > near-plane (0.05) → tidak di-clip
        eye = [
            k.x,                             # X: tetap di jalur
            cfg['eye_y'],                    # Y: tinggi mata pengemudi
            k.z + fwd_z * cfg['eye_z_fwd'],  # Z: maju mendekati kaca depan
        ]

        # ── Target: jauh ke depan di luar kendaraan ───────────────────────────
        target_pt = [
            k.x,                                      # X: lurus ke depan
            cfg['eye_y'] + cfg['tgt_y_dip'],          # Y: sedikit turun (lihat jalan)
            k.z + fwd_z * cfg['tgt_z_fwd'],           # Z: 15 unit di depan
        ]

        return eye, target_pt, [0.0, 1.0, 0.0]

    def _target_trackside(self):
        return [12.0, 3.5, -8.0], [0.0, 1.0, 0.0], [0.0, 1.0, 0.0]

    # ══════════════════════════════════════════════════════════════════════════
    #  APPLY KE OPENGL
    # ══════════════════════════════════════════════════════════════════════════
    def apply(self, kendaraan_list=None):
        """Hitung target, interpolasi lerp, terapkan gluLookAt."""
        if kendaraan_list is None:
            kendaraan_list = []

        if self.mode == CAM_OVERVIEW:
            eye_t, cen_t, up_t = self._target_overview()
            s = self._smooth_ov
        elif self.mode == CAM_DRIVER:
            eye_t, cen_t, up_t = self._target_driver(kendaraan_list)
            s = self._smooth_drv
        else:
            eye_t, cen_t, up_t = self._target_trackside()
            s = self._smooth_ov

        for i in range(3):
            self._eye[i]    = lerp(self._eye[i],    eye_t[i],  s)
            self._center[i] = lerp(self._center[i], cen_t[i],  s)
            self._up[i]     = lerp(self._up[i],     up_t[i],   s)

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