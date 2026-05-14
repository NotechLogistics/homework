import pygame
import pygame.freetype
from pygame.locals import *

FONT_PATH = {
    "黑体": "assets/font/黑体.ttf",
    "arial": "assets/font/arial.ttf",
}

TRANSPARENT = (0,0,0,0)
BLACK = (0,0,0)
BLUE = (52, 72, 120)
GREEN = (25, 149, 0)
RED = (255,0,0)
WHITE=(255,255,255)

class Image(pygame.sprite.Sprite):
    def __init__(self, surface, pos=None,size=None,
                 x=None, y=None, width=None, height=None):
        self.image = surface
        self.rect = self.image.get_rect()
        self.rect = self.set_rect(pos =pos,size = size,x = x, y = y, width = width, height = height)

        self.isavailable = True
        self.isvisible = True

    def set_rect(self, pos=None,size=None,x=None, y=None,center=False, width=None, height=None):
        rect = self.image.get_rect()
        rect = self.set_pos(rect, pos,x,y,center)
        rect = self.set_size(rect,size,width,height)
        self.rect = rect
        return rect
    def surface_update(self,rect):
        self.image = pygame.transform.scale(self.image, rect.size)
    def set_pos(self,rect = None, pos = None,x = None,y = None,center=False):
        if rect == None:
            rect = self.rect
        if center:
            if pos:
                rect.center = pos
            elif x != None and y != None:
                rect.center = (x, y)
            elif x != None:
                rect.centerx = x
            elif y != None:
                rect.centery = y
        else:
            if pos:
                rect.topleft = pos
            elif x != None and y != None:
                rect.topleft = (x, y)
            elif x != None:
                rect.x = x
            elif y != None:
                rect.y = y
        self.rect = rect
        return rect
    def set_size(self, rect=None,size = None,width = None,height = None):
        if rect == None:
            rect = self.rect
        if size:
            rect.size = size
        elif width != None and height != None:
            rect.size = (width, height)
        elif width != None and height == None:
            rect.height = rect.height * (width / rect.width)
            rect.width = width
        elif height != None and width == None:
            rect.width = rect.width * (height / rect.height)
            rect.height = height
        self.rect = rect
        self.surface_update(self.rect)
        return rect
    def move(self, dx=0, dy=0):
        return self.rect.move(dx, dy)
    def inflate(self, dx=0, dy=0):
        return self.rect.inflate(dx, dy)
    def draw(self, screen,rect = None,pos = None,x = None,y = None,center=False,size = None,width = None,height = None):
        if self.isvisible:
            if  pos or x != None or y != None or size or width != None or height != None:
                self.rect = self.set_rect(pos,size,x,y,center,width,height)
            elif rect:
                self.rect = rect
            self.surface_update(self.rect)
            screen.blit(self.image, self.rect)
    def is_clicked(self, event,father_pos = (0,0)):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (4,5):
                return
            if not self.isavailable:
                return
            rect = self.rect.move(father_pos)
            return rect.collidepoint(event.pos)
    def is_hovering(self, event,father_pos = (0,0)):
        if event.type == pygame.MOUSEMOTION:
            if not self.isavailable:
                return
            rect = self.rect.move(father_pos)
            return rect.collidepoint(event.pos)

def imageLoad(path,size = None,width = None,height = None):
    surface = pygame.image.load(path)
    return Image(surface,size=size,width=width,height=height)

def createTansparent(size,rbga = (0,0,0,0)):
    surface = pygame.Surface(size, pygame.SRCALPHA)  # 创建透明背景
    surface.fill(rbga)  # 填充透明背景
    return Image(surface,size=size)

def createFrame(image,color,size):
    """
    绘制边框
    :param image: 画布
    :param color: 边框颜色
    :param size: 边框粗细
    :return: 带边框的图片 -> Image
    """
    surface = createTansparent(image.rect.inflate(2*size,2*size).size)
    image.draw(surface.image, pos=(size, size))
    pygame.draw.rect(surface.image, color, surface.rect, size)
    return surface

class Text:
    @staticmethod
    def strong(font):
        font.strong = True
        return font
    @staticmethod
    def oblique(font):
        font.oblique = True
        return font
    @staticmethod
    def underline(font):
        font.underline = True
        return font
    @staticmethod
    def vertical(font):
        font.vertical = True
        return font
    @staticmethod
    def frame(image,frame_size,frame_color):
        return createFrame(image,frame_color,frame_size)
    @staticmethod
    def stroking(image,text,font,stroking_color,stroking_size):
        _ = Image(font.render(text,stroking_color)[0])
        _.draw(image.image, pos = image.move(stroking_size, 0).center, center=True)
        _.draw(image.image, pos = image.move(0, -stroking_size).center, center=True)
        _.draw(image.image, pos = image.move(-stroking_size, 0).center, center=True)
        _.draw(image.image, pos = image.move(0, stroking_size).center, center=True)
        _.draw(image.image, pos=image.move(-stroking_size, -stroking_size).center, center=True)
        _.draw(image.image, pos=image.move(stroking_size, stroking_size).center, center=True)
        _.draw(image.image, pos=image.move(stroking_size, -stroking_size).center, center=True)
        _.draw(image.image, pos=image.move(-stroking_size, stroking_size).center, center=True)
        return image
    @staticmethod
    def wrap(text, font, max_width):
        lines = []
        current_line = []
        last_line = []
        current_width = 0
        # 预计算常用标点符号
        punctuation = {'，', '。', '！', '？', '、', '；', '：', '”', '）', '》', '…'}
        for char in text:
            if char == "\n":
                lines.append(''.join(current_line))
                current_line = []
                current_width = 0
                continue
            # 获取字符宽度（考虑中英文字体差异）
            char_width = font.get_metrics(char)[0][4]
            _ = font.render(char)
            # 处理换行条件
            current_line.append(char)
            current_width += char_width
            if current_width >= max_width:

                if last_line and current_line == last_line:
                    lines.append(''.join(current_line))
                    current_line = []
                    last_line = []
                    current_width = 0
                    continue
                if char in punctuation:
                    if current_width - max_width >= char_width/2:
                        lines.append(''.join(current_line))
                        current_line = []
                        current_width = 0
                    else:
                        last_line = [current_line.pop(-2), current_line.pop(-1)]
                        if current_line:
                            lines.append(''.join(current_line))
                        current_line = last_line[::]
                        current_width = sum(map(lambda x: font.get_rect(x).width, last_line))
                else:
                    last_line = [current_line.pop(-1)]
                    lines.append(''.join(current_line))
                    current_line = last_line[::]
                    current_width = sum(map(lambda x: font.get_rect(x).width, last_line))
        if current_line:
            lines.append(''.join(current_line))
        return lines


def createText(text,font_style,color,size,
               stroking_size=0,stroking_color=TRANSPARENT,
               frame_size=0,frame_color=TRANSPARENT,
               margins=2, background_color = TRANSPARENT,
               vertical = False,strong = False,oblique = False,underline = False,
               iswarp = False,width = None,line_height = 1.2):
    pygame.freetype.init()
    font = pygame.freetype.Font(FONT_PATH[font_style], size)
    if vertical:
        font = Text.vertical(font)
    if strong:
        font = Text.strong(font)
    if oblique:
        font = Text.oblique(font)
    if underline:
        font = Text.underline(font)
    if iswarp and width:
        text = Text.wrap(text, font, width)
        line_height = int(font.get_sized_height() * line_height)
        height = line_height*len(text)
        y = 0
        text_surface = createTansparent((2*(stroking_size+margins)+width,2*(stroking_size+margins)+height),background_color)
        for line in text:
            _ = Image(font.render(line, color)[0])
            _.rect = _.set_pos(_.rect,x = 0,y = y)
            if stroking_size > 0:
                text_surface = Text.stroking(text_surface,line,font,stroking_color,stroking_size)
            _.draw(text_surface.image, pos = (margins, y + margins))
            y += line_height
    else:
        _ = Image(font.render(text, color)[0])
        text_surface = createTansparent(_.inflate(2*(stroking_size+margins),2*(stroking_size+margins)).size,background_color)
        if stroking_size > 0:
            text_surface = Text.stroking(text_surface,text,font,stroking_color,stroking_size)
        _.draw(text_surface.image, pos = text_surface.rect.center, center=True)
    if frame_size > 0:
        text_surface = Text.frame(text_surface,frame_size,frame_color)
    return text_surface

class Button(Image):
    def  __init__(self, text , size = None , width = None, height = None, font_size = 16,
                font_style = "黑体",color = BLACK,margins=2,vertical = False,strong = False):
        self.text = text
        self.font_size = font_size
        self.font_style = font_style
        self.color = color
        self.margins = margins
        self.vertical = vertical
        self.strong = strong
        #创建字体
        self.text_image = createText(text,font_style,color,font_size,margins=margins,vertical=vertical,strong=strong)
        #导入背景图片并初始化
        if not (size or width or height):
            size = self.text_image.rect.size
        self.background = imageLoad("assets/images/board.png",size,width,height)
        super().__init__(createTansparent(size).image)
        self.background.draw(self.image)
        #绘制字体
        self.text_image.draw(self.image,pos=self.rect.center,center=True)
    def update(self):
        self.image.fill(TRANSPARENT)
        self.background.draw(self.image)
        self.text_image.draw(self.image, pos=self.background.rect.center, center=True)



class ScrollBar(Image):
    def __init__(self, size, bg_color=(0, 0, 0, 0), bg_image=None , scroll_offset = 20 , isHorizontal = False):
        super().__init__(createTansparent(size).image)          # 创建初始化背景
        self.background = imageLoad(bg_image) if bg_image else createTansparent(size,bg_color)         # 创建背景图片
        self.images = []
        self.isHorizontal = isHorizontal          # 是否为水平滚动
        self.top = 0                 # 顶部位置,左侧
        self.end = self.rect.width if isHorizontal else self.rect.height          # 底部位置，右侧
        self.scroll_offset = scroll_offset          #单次滚动偏移量
        self.offset = 0          # 偏移量
        self.max = 0            # 最大坐标
        self.min = 0                # 最小坐标
    def add(self, image:Image,pos,isavailable=True):
        image.rect = image.set_pos(image.rect,pos = pos)
        image.isavailable = isavailable
        self.images.append(image)
    def is_scroll(self,event):
        if event.type == pygame.MOUSEWHEEL:
            self.change_offset(event.y)
    def change_offset(self,event):
        self.offset = self.scroll_offset  # 偏移量
        if event < 0:  # 向下滚动
            self.offset = -self.offset
        if self.isHorizontal:
            self.max = max([image.rect.bottomright[0] for image in self.images])
            self.min = min([image.rect.bottomleft[0] for image in self.images])
            if self.min +self.offset > self.top:
                # 左侧判定
                _ = self.top - (self.min)
                self.offset = _ if _ > 0 else 0  # 补齐偏移量
            elif self.max + self.offset < self.end:
                # 右侧判定
                _ = self.end - (self.max)
                self.offset = _ if _ < 0 else 0  # 补齐偏移量
        else:
            self.max = max([image.rect.bottomleft[1] for image in self.images])
            self.min = min([image.rect.topleft[1] for image in self.images])
            if self.min + self.offset > self.top:
                # 顶部判定
                _ = self.top - (self.min)
                self.offset = _ if _ > 0 else 0  # 补齐偏移量
            elif self.max + self.offset < self.end:
                # 底部判定
                _ = self.end - (self.max)
                self.offset = _ if _ < 0 else 0  # 补齐偏移量
        self.update()
        self.offset = 0
    def update(self):
        self.image.fill(TRANSPARENT)
        self.background.draw(self.image)
        for image in self.images:
            if self.isHorizontal:
                image.rect.x += self.offset
                if  image.rect.x > self.end or image.rect.topright[0] < self.top:
                    image.isavailable = False
                else:
                    image.isavailable = True
            else:
                image.rect.y += self.offset
                if image.rect.y > self.end or image.rect.bottomleft[1] < self.top:
                    image.isavailable = False
                else:
                    image.isavailable = True
            image.draw(self.image)
    def draw(self, screen,rect = None,pos = None,x = None,y = None,center=False,size = None,width = None,height = None):
        super().draw(screen,rect,pos,x,y,center,size,width,height)
        self.update()


