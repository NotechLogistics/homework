import pygame
from ui.image import UIElement,InputBox
class UIManager:
    def __init__(self):
        self.elements = []   # 所有顶层 UIElement
        self.focused_input = None   # 当前获得焦点的 InputBox 实例

    def add(self, elem: UIElement):
        self.elements.append(elem)

    def handle_event(self, event):
        # 按 z 降序排序
        for elem in sorted(self.elements, key=lambda e: e.z, reverse=True):
            if elem.handle_event(event):
                # 如果事件被某个 InputBox 消费，并且该 InputBox 变成了激活状态，则更新全局焦点
                if isinstance(elem, InputBox) and elem.active:
                    if self.focused_input != elem:
                        # 失活之前的焦点
                        if self.focused_input:
                            self.focused_input.active = False
                            self.focused_input._update_surface()
                        self.focused_input = elem
                return True
        return False
    def update(self, dt):
        for elem in sorted(self.elements, key=lambda e: e.z):
            if hasattr(elem, 'update'):
                elem.update(dt)

    def draw(self, screen):
        # 绘制时也要按 z 升序（从低到高），否则高层的会被底层覆盖
        for elem in sorted(self.elements, key=lambda e: e.z):
            elem.draw(screen)