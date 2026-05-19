import pygame
import pygame.freetype
from pygame.locals import *
from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple, List, Union

# ---------- 全局常量 ----------
FONT_PATH = {
    "黑体": "assets/font/黑体.ttf",
    "arial": "assets/font/arial.ttf",
}

TRANSPARENT = (0, 0, 0, 0)
BLACK = (0, 0, 0)
BLUE = (52, 72, 120)
GREEN = (25, 149, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# ---------- 简单图片加载函数（无状态） ----------
def load_image(path: str, size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
    """加载图片，可选缩放（仅在加载时缩放一次）"""
    try:
        surf = pygame.image.load(path).convert_alpha()
    except FileNotFoundError:
        # 创建一个占位表面，避免崩溃
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        surf.fill((255, 0, 255, 255))  # 品红色错误提示
        print(f"警告: 图片不存在 {path}")
    if size:
        surf = pygame.transform.smoothscale(surf, size)
    return surf

def create_transparent_surface(size: Tuple[int, int], color: Tuple[int, int, int, int] = TRANSPARENT) -> pygame.Surface:
    """创建带透明通道的表面"""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(color)
    return surf

# ---------- 文本渲染（带缓存） ----------
class TextRenderer:
    """文本渲染器，内部缓存渲染结果，提高性能"""
    @staticmethod
    @lru_cache(maxsize=128)
    def render(
        text: str,
        font_style: str,
        font_size: int,
        color: Tuple[int, int, int],
        background: Tuple[int, int, int, int] = TRANSPARENT,
        stroke_size: int = 0,
        stroke_color: Tuple[int, int, int, int] = TRANSPARENT,
        underline: bool = False,
        strong: bool = False,
        oblique: bool = False,
        vertical: bool = False,
    ) -> pygame.Surface:
        """
        渲染一行文字（无换行），支持描边、下划线等样式。
        返回带有透明通道的 Surface。
        """
        pygame.freetype.init()
        font_path = FONT_PATH.get(font_style, None)
        if not font_path or not Path(font_path).exists():
            # 回退到默认字体
            font = pygame.freetype.Font(None, font_size)
        else:
            font = pygame.freetype.Font(font_path, font_size)

        # 设置样式
        font.underline = underline
        font.strong = strong
        font.oblique = oblique
        font.vertical = vertical

        # 先渲染普通文本，获取尺寸
        rendered, rect = font.render(text, color)
        if stroke_size <= 0:
            # 无描边，直接返回
            if background != TRANSPARENT:
                # 带背景
                final = create_transparent_surface(rect.size, background)
                final.blit(rendered, (0, 0))
                return final
            return rendered

        # 有描边：创建一个稍大的表面，绘制8个方向的偏移文本 + 中心文本
        size = (rect.width + 2 * stroke_size, rect.height + 2 * stroke_size)
        final = create_transparent_surface(size, background)
        center_pos = (stroke_size, stroke_size)  # 文本在final中的位置

        # 偏移方向 (dx, dy)
        directions = [
            (-stroke_size, -stroke_size), (-stroke_size, 0), (-stroke_size, stroke_size),
            (0, -stroke_size), (0, stroke_size),
            (stroke_size, -stroke_size), (stroke_size, 0), (stroke_size, stroke_size)
        ]
        # 绘制描边文本
        stroke_text, _ = font.render(text, stroke_color)
        for dx, dy in directions:
            final.blit(stroke_text, (center_pos[0] + dx, center_pos[1] + dy))
        # 绘制中心文本
        final.blit(rendered, center_pos)
        return final

    @staticmethod
    def wrap_text(text: str, font: pygame.freetype.Font, max_width: int) -> List[str]:
        """
        将长文本按最大宽度换行，返回行列表。
        简单的贪心算法，不考虑标点避头尾，但已足够稳定。
        """
        lines = []
        words = list(text)  # 按字符切分（适合中文），如需英文按空格可另做处理
        current_line = []
        current_width = 0

        for ch in words:
            char_width = font.get_metrics(ch)[0][4]  # advance 宽度
            if current_width + char_width <= max_width:
                current_line.append(ch)
                current_width += char_width
            else:
                # 换行
                lines.append(''.join(current_line))
                current_line = [ch]
                current_width = char_width
        if current_line:
            lines.append(''.join(current_line))
        return lines

    @classmethod
    def render_wrapped(
        cls,
        text: str,
        font_style: str,
        font_size: int,
        color: Tuple[int, int, int],
        max_width: int,
        line_spacing: float = 1.2,
        background: Tuple[int, int, int, int] = TRANSPARENT,
        stroke_size: int = 0,
        stroke_color: Tuple[int, int, int, int] = TRANSPARENT,
        **kwargs
    ) -> pygame.Surface:
        """
        渲染自动换行的文本块。
        :param max_width: 每行最大宽度（像素）
        :param line_spacing: 行距系数，1.0为单倍行距
        :return: 包含多行文本的 Surface
        """
        pygame.freetype.init()
        font_path = FONT_PATH.get(font_style, None)
        if not font_path or not Path(font_path).exists():
            font = pygame.freetype.Font(None, font_size)
        else:
            font = pygame.freetype.Font(font_path, font_size)

        lines = cls.wrap_text(text, font, max_width)
        line_height = int(font.get_sized_height() * line_spacing)
        total_height = line_height * len(lines)
        surface = create_transparent_surface((max_width, total_height), background)

        y = 0
        for line in lines:
            # 渲染单行
            line_surf = cls.render(
                line, font_style, font_size, color,
                background=TRANSPARENT,
                stroke_size=stroke_size,
                stroke_color=stroke_color,
                **kwargs
            )
            # 水平居中（可选，这里左对齐，可以改为居中）
            x = 0
            surface.blit(line_surf, (x, y))
            y += line_height
        return surface

# ---------- 基础 UI 元素 ----------
class UIElement:
    """所有 UI 元素的基类，处理位置、可见性、点击检测"""
    def __init__(self, surface: pygame.Surface, x: int = 0, y: int = 0):
        self.image = surface
        self.rect = surface.get_rect(topleft=(x, y))
        self.visible = True
        self.enabled = True

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """绘制自身，支持父容器偏移"""
        if self.visible:
            screen.blit(self.image, (self.rect.x + offset_x, self.rect.y + offset_y))

    def handle_event(self, event: pygame.event.Event, offset_x: int = 0, offset_y: int = 0) -> bool:
        """
        处理鼠标事件，返回是否命中（用于事件冒泡）
        子类可重写。
        """
        if not self.enabled:
            return False
        if event.type == MOUSEBUTTONDOWN and event.button == 1:  # 左键
            global_pos = (event.pos[0] - offset_x, event.pos[1] - offset_y)
            if self.rect.collidepoint(global_pos):
                self.on_click()
                return True
        return False

    def on_click(self):
        """点击回调，子类重写"""
        pass

    def set_position(self, x: int, y: int):
        self.rect.topleft = (x, y)

    def set_center(self, x: int, y: int):
        self.rect.center = (x, y)

class Button(UIElement):
    """带文本的按钮"""
    def __init__(
        self,
        text: str,
        x: int = 0,
        y: int = 0,
        font_style: str = "黑体",
        font_size: int = 20,
        text_color: Tuple[int, int, int] = BLACK,
        bg_image_path: str = "assets/images/board.png",
        padding: int = 10,
    ):
        # 渲染文本
        text_surf = TextRenderer.render(text, font_style, font_size, text_color)
        # 加载背景图片，尺寸适配文本 + 内边距
        bg_surf = load_image(bg_image_path)
        width = text_surf.get_width() + 2 * padding
        height = text_surf.get_height() + 2 * padding
        if bg_surf.get_size() != (width, height):
            bg_surf = pygame.transform.smoothscale(bg_surf, (width, height))

        # 合成最终按钮表面
        final = bg_surf.copy()
        text_x = (width - text_surf.get_width()) // 2
        text_y = (height - text_surf.get_height()) // 2
        final.blit(text_surf, (text_x, text_y))

        super().__init__(final, x, y)
        self.callback = None

    def on_click(self):
        if self.callback:
            self.callback()

    def set_callback(self, callback):
        self.callback = callback

class ScrollView(UIElement):
    """
    可滚动区域，包含多个子 UIElement。
    修复了原版坐标永久漂移的问题：子控件的 rect 保持原始逻辑位置，
    滚动时只改变绘制偏移量，可见性通过裁剪判断。
    """
    def __init__(
        self,
        view_size: Tuple[int, int],
        x: int = 0,
        y: int = 0,
        bg_color: Tuple[int, int, int, int] = (200, 200, 200, 255),
        scroll_speed: int = 20,
        horizontal: bool = False,
    ):
        """
        :param view_size: 滚动区域的视口大小 (width, height)
        :param scroll_speed: 鼠标滚轮每次滚动偏移像素
        :param horizontal: 是否水平滚动
        """
        # 创建一个视口表面，作为滚动区域的“窗口”
        self.viewport = create_transparent_surface(view_size, bg_color)
        super().__init__(self.viewport, x, y)
        self.children: List[UIElement] = []          # 所有子控件（逻辑坐标，相对于内容区域原点）
        self.scroll_offset = 0                       # 当前滚动偏移量（正数表示向下/右滚动）
        self.scroll_speed = scroll_speed
        self.horizontal = horizontal
        self.content_size: Optional[Tuple[int, int]] = None   # 内容总尺寸，在 add 后自动计算

    def add(self, child: UIElement, local_x: int, local_y: int):
        """添加子控件，local_x, local_y 是相对于内容区域左上角的位置"""
        child.set_position(local_x, local_y)
        self.children.append(child)
        self._update_content_size()

    def _update_content_size(self):
        """计算所有子控件占据的总尺寸"""
        if not self.children:
            self.content_size = self.viewport.get_size()
            return
        max_x = max(c.rect.right for c in self.children)
        max_y = max(c.rect.bottom for c in self.children)
        self.content_size = (max(max_x, self.viewport.get_width()), max(max_y, self.viewport.get_height()))

    def handle_event(self, event: pygame.event.Event, offset_x: int = 0, offset_y: int = 0) -> bool:
        """处理滚动事件及子控件事件，注意偏移叠加"""
        if not self.enabled or not self.visible:
            return False

        # 处理滚轮事件
        if event.type == pygame.MOUSEWHEEL:
            # 注意 event.y: 正为上滚，负为下滚
            delta = event.y * self.scroll_speed
            new_offset = self.scroll_offset - delta if not self.horizontal else self.scroll_offset - delta
            # 限制滚动范围
            max_offset = 0
            if self.horizontal and self.content_size:
                max_offset = max(0, self.content_size[0] - self.viewport.get_width())
            elif self.content_size:
                max_offset = max(0, self.content_size[1] - self.viewport.get_height())
            self.scroll_offset = max(0, min(max_offset, new_offset))
            return True   # 滚轮事件已处理

        # 传递给子控件，注意子控件坐标需要减去滚动偏移
        for child in reversed(self.children):  # 后添加的在上层
            child_offset_x = offset_x + self.rect.x - (self.scroll_offset if self.horizontal else 0)
            child_offset_y = offset_y + self.rect.y - (self.scroll_offset if not self.horizontal else 0)
            if child.handle_event(event, child_offset_x, child_offset_y):
                return True
        return False

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        if not self.visible:
            return
        # 先清空视口表面
        self.viewport.fill((0, 0, 0, 0))  # 完全透明，背景由外部或自己填充
        # 绘制背景色（如果需要）
        # 这里简单用灰色填充一下例子，实际可以设置纹理
        self.viewport.fill((220, 220, 220))

        # 遍历子控件，根据滚动偏移和视口区域进行裁剪
        clip_rect = self.viewport.get_rect()
        for child in self.children:
            # 子控件在视口中的逻辑位置（相对滚动区域原点）
            child_local_x = child.rect.x - (self.scroll_offset if self.horizontal else 0)
            child_local_y = child.rect.y - (self.scroll_offset if not self.horizontal else 0)
            child_rect_in_view = pygame.Rect(child_local_x, child_local_y, child.rect.width, child.rect.height)
            if child_rect_in_view.colliderect(clip_rect):
                # 绘制到视口表面，位置减去滚动偏移
                self.viewport.blit(child.image, (child_local_x, child_local_y))
        # 将视口绘制到屏幕上
        screen.blit(self.viewport, (self.rect.x + offset_x, self.rect.y + offset_y))

# ---------- 便捷函数，兼容旧版 API ----------
def create_text(
    text: str,
    font_style: str,
    color: Tuple[int, int, int],
    size: int,
    stroke_size: int = 0,
    stroke_color: Tuple[int, int, int, int] = TRANSPARENT,
    frame_size: int = 0,
    frame_color: Tuple[int, int, int] = BLACK,
    margins: int = 2,
    background_color: Tuple[int, int, int, int] = TRANSPARENT,
    vertical: bool = False,
    strong: bool = False,
    oblique: bool = False,
    underline: bool = False,
    wrap_width: Optional[int] = None,
    line_height: float = 1.2,
) -> UIElement:
    """
    创建文本控件，支持描边、边框、自动换行。
    返回一个 UIElement，可直接绘制或添加到 ScrollView。
    """
    if wrap_width:
        surf = TextRenderer.render_wrapped(
            text, font_style, size, color, wrap_width, line_height,
            background_color, stroke_size, stroke_color,
            underline=underline, strong=strong, oblique=oblique, vertical=vertical
        )
    else:
        surf = TextRenderer.render(
            text, font_style, size, color, background_color,
            stroke_size, stroke_color, underline, strong, oblique, vertical
        )

    # 添加边框
    if frame_size > 0:
        padded = create_transparent_surface(
            (surf.get_width() + 2 * frame_size, surf.get_height() + 2 * frame_size),
            background_color
        )
        padded.blit(surf, (frame_size, frame_size))
        pygame.draw.rect(padded, frame_color, padded.get_rect(), frame_size)
        surf = padded

    return UIElement(surf)

def create_image(path: str, size: Optional[Tuple[int, int]] = None) -> UIElement:
    """加载图片并创建 UIElement"""
    surf = load_image(path, size)
    return UIElement(surf)

# ---------- 使用示例 （放在 if __name__ == "__main__" 中测试）----------
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    # 创建滚动视图
    scroll = ScrollView((400, 300), x=100, y=100, bg_color=(200, 200, 200, 255))
    # 添加一些文字和按钮
    text_elem = create_text(
        "这是一个很长的文本示例，用来测试自动换行功能。我们希望这段文字能够在滚动区域内正确显示并且支持鼠标滚轮。",
        "黑体", BLACK, 20,
        wrap_width=380,
        background_color=(255, 255, 255, 200),
        stroke_size=1,
        stroke_color=(0,0,0,100)
    )
    scroll.add(text_elem, 10, 10)

    btn = Button("点我", font_size=18, bg_image_path="assets/images/board.png")
    btn.set_callback(lambda: print("按钮被点击"))
    scroll.add(btn, 10, 100)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            scroll.handle_event(event)  # 传递事件给滚动区域

        screen.fill((150, 150, 150))
        scroll.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()