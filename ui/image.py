import pygame
import pygame.freetype
from pygame.locals import *
from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple, List, Union
from time import time

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
YELLOW = (255, 255, 128)
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
    def __init__(self, surface: pygame.Surface, x: int = 0, y: int = 0, z: int = 0):
        """
        :param surface: 图片表面
        :param x: 左上角 x 坐标
        :param y: 左上角 y 坐标
        :param z: 层级（越大越靠前）
        """
        self.image = surface
        self.rect = surface.get_rect(topleft=(x, y))
        self.visible = True
        self.enabled = True
        self.z = z

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
    def update(self, dt):
        """更新状态，dt为距离上次调用的秒数，子类可重写"""
        pass

    def on_click(self):
        """点击回调，子类重写"""
        pass

    def set_position(self, x: int, y: int):
        self.rect.topleft = (x, y)

    def set_center(self, x: int, y: int):
        self.rect.center = (x, y)

class Button(UIElement):
    def __init__(
        self,
        text: str,
        x: int = 0,
        y: int = 0,
        size: Optional[Tuple[int, int]] = None,   # 新增参数：固定按钮尺寸
        font_style: str = "黑体",
        font_size: int = 20,
        text_color: Tuple[int, int, int] = BLACK,
        bg_image_path: str = "assets/images/board.png",
        padding: int = 10,
        z: int = 0,
    ):
        # 渲染文本
        text_surf = TextRenderer.render(text, font_style, font_size, text_color)

        if size is not None:
            # 固定尺寸模式
            width, height = size
            # 加载背景并缩放到固定尺寸
            bg_surf = load_image(bg_image_path)
            bg_surf = pygame.transform.smoothscale(bg_surf, (width, height))
            # 创建最终按钮表面
            final = bg_surf.copy()
            # 文本居中（若文本超出尺寸，会被裁剪，调用者需确保足够空间）
            text_x = (width - text_surf.get_width()) // 2
            text_y = (height - text_surf.get_height()) // 2
            final.blit(text_surf, (text_x, text_y))
        else:
            # 自动尺寸模式（原有逻辑）
            bg_surf = load_image(bg_image_path)
            width = text_surf.get_width() + 2 * padding
            height = text_surf.get_height() + 2 * padding
            if bg_surf.get_size() != (width, height):
                bg_surf = pygame.transform.smoothscale(bg_surf, (width, height))
            final = bg_surf.copy()
            text_x = (width - text_surf.get_width()) // 2
            text_y = (height - text_surf.get_height()) // 2
            final.blit(text_surf, (text_x, text_y))

        super().__init__(final, x, y, z)
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
        :param x: 滚动区域左上角 x 坐标
        :param y: 滚动区域左上角 y 坐标
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

        # 滚轮事件依然由 ScrollView 自己优先处理
        if event.type == pygame.MOUSEWHEEL:
            delta = event.y * self.scroll_speed
            new_offset = self.scroll_offset - delta if not self.horizontal else self.scroll_offset - delta
            max_offset = 0
            if self.horizontal and self.content_size:
                max_offset = max(0, self.content_size[0] - self.viewport.get_width())
            elif self.content_size:
                max_offset = max(0, self.content_size[1] - self.viewport.get_height())
            self.scroll_offset = max(0, min(max_offset, new_offset))
            return True

        # 按 z 降序排序，同 z 则按添加顺序（保持稳定）
        sorted_children = sorted(self.children, key=lambda c: c.z, reverse=True)
        for child in sorted_children:
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
    :param text: 文本内容
    :param font_style: 字体样式，如 "黑体"
    :param color: 字体颜色，如 (0, 0, 0)
    :param size: 字体大小
    :param stroke_size: 描边大小，0 表示无描边
    :param stroke_color: 描边颜色
    :param frame_size: 边框大小，0 表示无边框
    :param frame_color: 边框颜色
    :param margins: 内边距
    :param background_color: 背景颜色
    :param vertical: 是否垂直排列
    :param strong: 是否加粗
    :param oblique: 是否斜体
    :param underline: 是否下划线
    :param wrap_width: 自动换行的最大宽度，None 表示不换
    :param line_height: 行距系数，1.0 为单倍行距
    :return: UIElement
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

class InputBox(UIElement):
    """
    单行文本输入框，支持：
    - 鼠标点击激活/失活
    - 键盘输入字符（可限制字符类型）
    - 左右箭头移动光标，Home/End，Backspace，Delete
    - 密码模式（显示为*）
    - 占位符文本（未激活且无内容时显示）
    - 最大长度限制
    - 光标自动滚动（当光标超出可视区域时）
    - 光标闪烁
    """
    _focused_instance = None   # 类变量焦点管理
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        font_style: str = "黑体",
        font_size: int = 24,
        text_color: Tuple[int, int, int] = BLACK,
        bg_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        border_color: Tuple[int, int, int] = (100, 100, 100),
        border_width: int = 2,
        active_border_color: Tuple[int, int, int] = (0, 100, 200),
        placeholder: str = "",
        placeholder_color: Tuple[int, int, int] = (150, 150, 150),
        max_length: int = 100,
        password_char: str = None,
        allowed_chars: str = None,   # 例如 "0123456789" 只允许数字，None 表示允许所有可打印字符
        z: int = 0,
    ):
        """
        :param placeholder: 占位文字（输入框为空且未激活时显示）
        :param password_char: 密码掩码字符，如果为 None 则显示真实文本
        :param allowed_chars: 允许输入的字符集，None 表示允许所有可打印字符（不包括控制键）
        """
        self.width = width
        self.height = height
        self.font_style = font_style
        self.font_size = font_size
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.active_border_color = active_border_color
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.max_length = max_length
        self.password_char = password_char
        self.allowed_chars = allowed_chars

        # 文本缓冲区
        self.text = ""           # 真实文本（未掩码）
        self.cursor_pos = 0      # 光标位置（字符索引）
        self.active = False      # 是否激活
        self.cursor_visible = True
        self.last_blink_time = time()
        self.blink_interval = 0.5  # 光标闪烁间隔（秒）

        # 滚动偏移（像素）
        self.scroll_offset = 0

        # 创建表面
        surface = self._create_surface()
        super().__init__(surface, x, y, z)

        # 加载字体（用于测量文本宽度）
        pygame.freetype.init()
        font_path = FONT_PATH.get(font_style, None)
        if not font_path or not Path(font_path).exists():
            self.font = pygame.freetype.Font(None, font_size)
        else:
            self.font = pygame.freetype.Font(font_path, font_size)

    def _create_surface(self) -> pygame.Surface:
        """创建输入框的背景表面（包含背景色和边框）"""
        surf = create_transparent_surface((self.width, self.height), self.bg_color)
        # 绘制边框
        border_clr = self.active_border_color if self.active else self.border_color
        pygame.draw.rect(surf, border_clr, surf.get_rect(), self.border_width)
        return surf

    def _get_display_text(self) -> str:
        """获取用于显示的文本（如果是密码模式则返回掩码）"""
        if self.password_char and self.password_char is not None:
            return self.password_char * len(self.text)
        return self.text

    def _get_text_surface(self) -> pygame.Surface:
        """渲染当前显示的文本（带缓存，但每次文本改变都会重新调用）"""
        display_text = self._get_display_text()
        if not display_text and not self.active and self.placeholder:
            # 显示占位符
            return TextRenderer.render(
                self.placeholder, self.font_style, self.font_size,
                self.placeholder_color, background=TRANSPARENT
            )
        return TextRenderer.render(
            display_text, self.font_style, self.font_size,
            self.text_color, background=TRANSPARENT
        )

    def _update_surface(self):
        """重新生成输入框表面（文本 + 背景 + 光标）"""
        # 重新创建基础背景（因为激活状态边框颜色可能改变）
        self.image = self._create_surface()
        # 计算文本绘制区域（留出左右内边距，避免太靠边）
        padding = 8
        text_area_width = self.width - 2 * padding
        text_surf = self._get_text_surface()
        text_width = text_surf.get_width()

        # 水平滚动：确保光标在可视区域内
        # 光标位置像素（基于当前文本）
        display_text = self._get_display_text()
        if self.cursor_pos == 0:
            cursor_pixel = 0
        else:
            # 获取光标前子串的宽度
            prefix = display_text[:self.cursor_pos]
            if prefix:
                # 临时测量宽度
                prefix_surf = TextRenderer.render(
                    prefix, self.font_style, self.font_size,
                    self.text_color, background=TRANSPARENT
                )
                cursor_pixel = prefix_surf.get_width()
            else:
                cursor_pixel = 0

        # 滚动调整：让光标出现在 text_area_width 内
        if cursor_pixel < self.scroll_offset:
            self.scroll_offset = cursor_pixel
        elif cursor_pixel > self.scroll_offset + text_area_width:
            self.scroll_offset = cursor_pixel - text_area_width
        # 避免滚动过头（比如文本很短时滚动不应为负）
        self.scroll_offset = max(0, min(self.scroll_offset, max(0, text_width - text_area_width)))

        # 裁剪文本区域（只绘制可视部分）
        clip_rect = pygame.Rect(padding, 0, text_area_width, self.height)
        # 将文本表面绘制到 image 上，考虑滚动偏移
        x_pos = padding - self.scroll_offset
        y_pos = (self.height - text_surf.get_height()) // 2
        self.image.blit(text_surf, (x_pos, y_pos))

        # 绘制光标（仅在激活状态且光标闪烁可见）
        if self.active and self.cursor_visible:
            # 计算光标位置（基于当前滚动偏移）
            cursor_x = padding + cursor_pixel - self.scroll_offset
            if 0 <= cursor_x <= self.width - 2:
                cursor_height = int(self.font.get_sized_height() * 0.7)
                cursor_y = (self.height - cursor_height) // 2
                pygame.draw.rect(self.image, self.text_color, (cursor_x, cursor_y, 2, cursor_height))

    def handle_event(self, event: pygame.event.Event, offset_x: int = 0, offset_y: int = 0) -> bool:
        if not self.enabled or not self.visible:
            return False

        # 计算全局鼠标位置下的点击检测
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            local_pos = (event.pos[0] - offset_x, event.pos[1] - offset_y)
            if self.rect.collidepoint(local_pos):
                # 让其他输入框失活
                if InputBox._focused_instance and InputBox._focused_instance != self:
                    InputBox._focused_instance.active = False
                    InputBox._focused_instance._update_surface()
                self.active = True
                InputBox._focused_instance = self
                # 开启文本输入和按键重复
                pygame.key.start_text_input()
                pygame.key.set_repeat(500, 30)   # 延迟500ms后每30ms重复
                self._update_surface()
                return True
            else:
                if self.active:
                    self.active = False
                    if InputBox._focused_instance == self:
                        InputBox._focused_instance = None
                    # 关闭文本输入（可选）
                    pygame.key.stop_text_input()
                    pygame.key.set_repeat(0)   # 关闭重复
                    self._update_surface()
                return False

        # 只有激活状态才处理键盘事件
        if self.active:
                # 修复2：优先处理 TEXTINPUT 事件
                if event.type == TEXTINPUT:
                    filtered = self._filter_text(event.text)
                    if filtered and len(self.text) + len(filtered) <= self.max_length:
                        self.text = self.text[:self.cursor_pos] + filtered + self.text[self.cursor_pos:]
                        self.cursor_pos += len(filtered)
                        self._update_surface()
                    return True

                elif event.type == KEYDOWN:
                    self._handle_keydown(event)
                    self._update_surface()
                    return True

        # 光标闪烁计时（非事件驱动，但为了简单，在更新中处理也可以，这里放在 handle_event 只是为了统一）
        # 实际闪烁应该在 update 中处理，但为了避免每帧调用，可以单独提供一个 update 方法。
        return False

    def _handle_keydown(self, event):
        """处理按键"""
        key = event.key
        mod = event.mod

        # 处理退格
        if key == K_BACKSPACE:
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
        # 删除
        elif key == K_DELETE:
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
        # 左箭头
        elif key == K_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
        # 右箭头
        elif key == K_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
        # Home
        elif key == K_HOME:
            self.cursor_pos = 0
        # End
        elif key == K_END:
            self.cursor_pos = len(self.text)
        # 回车（可自定义提交行为，这里仅失活）
        elif key == K_RETURN or key == K_KP_ENTER:
            self.active = False
        # Ctrl+V 粘贴（简单实现，需要 pygame 支持获取剪贴板）
        elif key == K_v and (mod & KMOD_CTRL):
            # 注意：pygame 2.0+ 支持 pygame.scrap 模块，这里演示简单方式
            try:
                import pygame.scrap
                pygame.scrap.init()
                clipboard = pygame.scrap.get(pygame.SCRAP_TEXT).decode('utf-8')
                # 过滤合法字符
                filtered = self._filter_text(clipboard)
                if len(self.text) + len(filtered) <= self.max_length:
                    self.text = self.text[:self.cursor_pos] + filtered + self.text[self.cursor_pos:]
                    self.cursor_pos += len(filtered)
            except:
                pass

    def _filter_text(self, text: str) -> str:
        """根据 allowed_chars 过滤文本"""
        if self.allowed_chars is None:
            return text
        return ''.join(ch for ch in text if ch in self.allowed_chars)

    def update(self, dt: float):
        """需要每帧调用来更新光标闪烁和重绘（可选）"""
        if self.active:
            now = time()
            if now - self.last_blink_time >= self.blink_interval:
                self.cursor_visible = not self.cursor_visible
                self.last_blink_time = now
                self._update_surface()

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """确保绘制前表面是最新的"""
        # 每次绘制前主动更新（确保文本变化后重绘）
        self._update_surface()
        super().draw(screen, offset_x, offset_y)

    def get_text(self) -> str:
        return self.text

    def set_text(self, text: str):
        """设置文本内容，光标置于末尾"""
        self.text = text[:self.max_length]
        self.cursor_pos = len(self.text)
        self._update_surface()

    def clear(self):
        self.set_text("")

from typing import List, Optional, Tuple, Callable

class FormPanel(UIElement):
    """
    表单面板：包含多个带标签的输入框和多个按钮。
    所有子控件绘制在一个透明表面上，可整体移动。
    """
    def __init__(
        self,
        x: int, y: int,
        panel_width: int,
        input_labels: List[str],          # 文本框前面的标题文本列表
        input_defaults: Optional[List[str]] = None,  # 输入框默认文本（可选）
        button_texts: Optional[List[str]] = None,    # 按钮文字列表
        button_callbacks: Optional[List[Callable]] = None,  # 按钮回调函数列表
        label_font_style: str = "黑体",
        label_font_size: int = 20,
        label_color: Tuple[int, int, int] = BLACK,
        input_font_style: str = "黑体",
        input_font_size: int = 20,
        input_text_color: Tuple[int, int, int] = BLACK,
        input_bg_color: Tuple[int, int, int, int] = (255,255,255,255),
        input_border_color: Tuple[int, int, int] = (100,100,100),
        input_active_border_color: Tuple[int, int, int] = (0,100,200),
        input_height: int = 35,
        input_password_char: Optional[str] = None,
        password_flags: Optional[List[bool]] = None,
        button_font_style: str = "黑体",
        button_font_size: int = 20,
        button_text_color: Tuple[int, int, int] = WHITE,
        button_bg_image: str = "assets/images/board.png",  # 按钮背景图
        button_padding: int = 10,
        label_input_gap: int = 5,          # 标题与输入框的间距（像素）
        row_gap: int = 15,                 # 行间距（上一行输入框与下一行标题的间距）
        button_gap: int = 20,              # 按钮之间的间距
        margin_left: int = 20,             # 左边距
        margin_top: int = 20,              # 上边距
        background_color: Tuple[int, int, int, int] = (240,240,240,200),  # 面板背景色（半透）
        border_width: int = 2,
        border_color: Tuple[int, int, int] = (100,100,100),
        z: int = 0,
    ):
        # 保存参数
        self.panel_width = panel_width
        self.input_labels = input_labels
        self.input_defaults = input_defaults or [""] * len(input_labels)
        self.button_texts = button_texts or []
        self.button_callbacks = button_callbacks or []
        self.label_font_style = label_font_style
        self.label_font_size = label_font_size
        self.label_color = label_color
        self.input_font_style = input_font_style
        self.input_font_size = input_font_size
        self.input_text_color = input_text_color
        self.input_bg_color = input_bg_color
        self.input_border_color = input_border_color
        self.input_active_border_color = input_active_border_color
        self.input_height = input_height
        self.input_password_char = input_password_char
        self.button_font_style = button_font_style
        self.button_font_size = button_font_size
        self.button_text_color = button_text_color
        self.button_bg_image = button_bg_image
        self.button_padding = button_padding
        self.label_input_gap = label_input_gap
        self.row_gap = row_gap
        self.button_gap = button_gap
        self.margin_left = margin_left
        self.margin_top = margin_top
        self.background_color = background_color
        self.border_width = border_width
        self.border_color = border_color
        self.password_flags = password_flags or [False] * len(input_labels)

        # 计算面板总高度
        self.input_boxes = []      # 存储 InputBox 实例
        self.labels = []           # 存储标题的 UIElement
        self.buttons = []          # 存储 Button 实例

        y_offset = margin_top
        # 创建每一行：标签 + 输入框
        for i, label_text in enumerate(input_labels):
            # 创建标签（静态文本）
            label = create_text(
                label_text, label_font_style, label_color, label_font_size,
                background_color=TRANSPARENT
            )
            # 标签放在左边
            label.set_position(margin_left, y_offset)
            self.labels.append(label)

            # 输入框宽度 = 面板宽度 - 左边距 - 右边距（右边距固定20）
            input_width = panel_width - margin_left - 20
            # 输入框放在标签下方（垂直排列），所以标签和输入框是上下关系
            # 标签底部到输入框顶部有 label_input_gap 间距
            input_y = y_offset + label.image.get_height() + label_input_gap
            is_password = self.password_flags[i] if i < len(self.password_flags) else False
            pwd_char = input_password_char if is_password else None
            input_box = InputBox(
                x=margin_left, y=input_y, width=input_width, height=input_height,
                font_style=input_font_style, font_size=input_font_size,
                text_color=input_text_color, bg_color=input_bg_color,
                border_color=input_border_color, active_border_color=input_active_border_color,
                placeholder="", max_length=100,password_char=pwd_char,
                allowed_chars=None, z=z+1  # 确保输入框在面板之上（便于点击）
            )
            input_box.set_text(self.input_defaults[i])
            self.input_boxes.append(input_box)

            # 更新 y_offset 到本行底部（输入框底部）
            y_offset = input_y + input_height + row_gap

        # 创建按钮区域（水平排列或垂直排列，这里水平居中排列）
        if button_texts:
            # 计算按钮总宽度
            btn_widths = []
            for btn_text in button_texts:
                # 临时计算按钮文本宽度
                font = pygame.freetype.Font(FONT_PATH.get(button_font_style, None), button_font_size)
                text_rect = font.get_rect(btn_text)
                btn_w = text_rect.width + 2 * button_padding
                btn_widths.append(btn_w)
            total_btns_width = sum(btn_widths) + max(0, len(button_texts)-1) * button_gap
            start_x = margin_left + (panel_width - margin_left - 20 - total_btns_width) // 2
            current_x = start_x
            for i, btn_text in enumerate(button_texts):
                btn = Button(
                    text=btn_text, x=int(current_x), y=y_offset,
                    font_style=button_font_style, font_size=button_font_size,
                    text_color=button_text_color, bg_image_path=button_bg_image,
                    padding=button_padding
                )
                if i < len(button_callbacks) and button_callbacks[i]:
                    btn.set_callback(button_callbacks[i])
                self.buttons.append(btn)
                current_x += btn_widths[i] + button_gap
            y_offset += self.buttons[0].rect.height + margin_top  # 增加底部留白

        total_height = y_offset

        # 创建面板表面
        panel_surface = create_transparent_surface((panel_width, total_height), background_color)
        # 绘制边框
        pygame.draw.rect(panel_surface, border_color, panel_surface.get_rect(), border_width)

        # 初始化 UIElement
        super().__init__(panel_surface, x, y, z)

        # 子控件列表（用于事件转发和绘制）
        self._children = self.labels + self.input_boxes + self.buttons

    def handle_event(self, event: pygame.event.Event, offset_x: int = 0, offset_y: int = 0) -> bool:
        """将事件转发给子控件（需要将屏幕坐标转换为面板内相对坐标）"""
        if not self.enabled or not self.visible:
            return False

        # 计算面板的全局偏移（面板自身的偏移 + 父容器传入的偏移）
        panel_global_x = self.rect.x + offset_x
        panel_global_y = self.rect.y + offset_y

        # 先让输入框和按钮处理事件（按 z 降序，但这里简单按列表顺序即可）
        # 注意：需要传递给子控件的偏移是面板全局偏移 + 子控件自身的位置已经在子控件的 rect 中体现
        # 子控件的 rect 是相对于面板左上角的，所以它们的绝对坐标 = panel_global_xy + child.rect.topleft
        # 因此在调用 child.handle_event 时，传入的偏移应该是 panel_global_xy
        for child in self._children:
            if child.handle_event(event, panel_global_x, panel_global_y):
                return True
        return False

    def draw(self, screen: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """先绘制面板背景（自身 image），再绘制子控件到面板表面"""
        if not self.visible:
            return
        # 绘制面板背景（边框等已在初始化时绘制，但如果有动态变化可重新绘制）
        # 为了性能，我们不再重绘整个面板，而是直接将面板表面 blit 到屏幕
        # 但是子控件需要绘制到面板表面上，而不是直接绘制到屏幕。
        # 因此我们需要先清空面板表面，然后绘制所有子控件到面板表面，最后把面板表面 blit 到屏幕。
        # 注意：面板表面是 self.image

        # 清空面板表面（保留背景色和边框）
        self.image.fill(self.background_color)
        pygame.draw.rect(self.image, self.border_color, self.image.get_rect(), self.border_width)

        # 将所有子控件绘制到面板表面上（不需要偏移，因为子控件的 rect 是相对于面板的）
        for child in self._children:
            # 子控件直接绘制到 self.image 上，位置即为 child.rect.topleft
            child.draw(self.image)  # 注意：这里传入的是面板表面，不是屏幕

        # 将面板表面绘制到屏幕
        screen.blit(self.image, (self.rect.x + offset_x, self.rect.y + offset_y))

    def get_input_values(self) -> List[str]:
        """返回所有输入框的当前文本"""
        return [ib.get_text() for ib in self.input_boxes]

    def set_input_values(self, values: List[str]):
        """设置所有输入框的文本"""
        for ib, val in zip(self.input_boxes, values):
            ib.set_text(val)
    def clear_inputs(self):
        """清空所有输入框"""
        for ib in self.input_boxes:
            ib.clear()