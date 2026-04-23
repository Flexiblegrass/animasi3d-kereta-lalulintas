import glfw
import math
from OpenGL.GL import *
from OpenGL.GLU import *

class Camera:
    def __init__(self):
        self.yaw   = 30.0
        self.pitch = 28.0
        self.dist  = 22.0
        self._mouse_last = None
        self._mouse_down = False

    def register_callbacks(self, window):
        glfw.set_key_callback(window,          self._key_cb)
        glfw.set_mouse_button_callback(window, self._mouse_btn_cb)
        glfw.set_cursor_pos_callback(window,   self._cursor_cb)
        glfw.set_scroll_callback(window,       self._scroll_cb)

    def _key_cb(self, window, key, scancode, action, mods):
        if action in (glfw.PRESS, glfw.REPEAT):
            if key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(window, True)
            elif key == glfw.KEY_EQUAL:
                self.dist = max(5.0, self.dist - 1.5)
            elif key == glfw.KEY_MINUS:
                self.dist = min(50.0, self.dist + 1.5)

    def _mouse_btn_cb(self, window, button, action, mods):
        if button == glfw.MOUSE_BUTTON_LEFT:
            self._mouse_down = (action == glfw.PRESS)
            if self._mouse_down:
                self._mouse_last = glfw.get_cursor_pos(window)

    def _cursor_cb(self, window, xpos, ypos):
        if self._mouse_down and self._mouse_last:
            dx = xpos - self._mouse_last[0]
            dy = ypos - self._mouse_last[1]
            self.yaw   += dx * 0.4
            self.pitch  = max(5.0, min(85.0, self.pitch + dy * 0.3))
            self._mouse_last = (xpos, ypos)

    def _scroll_cb(self, window, xoff, yoff):
        self.dist = max(5.0, min(50.0, self.dist - yoff * 1.0))

    def apply(self):
        pr = math.radians(self.pitch)
        yr = math.radians(self.yaw)
        cx = self.dist * math.cos(pr) * math.sin(yr)
        cy = self.dist * math.sin(pr)
        cz = self.dist * math.cos(pr) * math.cos(yr)
        glLoadIdentity()
        glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 20.0, 10.0, 1.0])
        gluLookAt(cx, cy, cz,  0, 1, 0,  0, 1, 0)