import pygame
from ui import image
import constant
class Button(image.Button):
    def __init__(self,text,path,x):
        super().__init__(
            text="",
            font_size=1,
            x=constant.SCREEN_WIDE / 2 + x,
            y=constant.SCREEN_HIGH / 2 - 200,
            text_color=image.BLACK,
            bg_image_path=constant.GENERAL_IMAGE_PATH + path,
            size=(210,400),
        )
        self.title = image.create_text(text, font_style="黑体", size=68, color=image.BLACK,stroke_color=image.WHITE,stroke_size=1,vertical=True)
    def draw(self, screen):
        self.title.set_position(self.rect.width - self.title.rect.width - 50, 40)
        self.title.draw(self.image)
        super().draw(screen)

class User(image.UIElement):
    def __init__(self,icon_path,z=0):
        super().__init__(image.create_transparent_surface((100,100), color=image.TRANSPARENT),z = z)
        self._children = []
        
        self.board = image.UIElement(image.load_image(constant.BOARD_IMAGE_PATH, size=(83.5, 100)), z=0)
        self._children.append(self.board)

        self.icon = image.UIElement(image.load_image(constant.GENERAL_IMAGE_PATH + icon_path, size=(83.5, 100)), z=0)
        self.icon.set_center(self.board.rect.width//2, self.board.rect.height//2)
        self._children.append(self.icon)
    
    def draw(self, screen):
        self.image.fill(image.TRANSPARENT)
        for child in self._children:
            child.draw(self.image)
        super().draw(screen)
        

class UserBar(image.UIElement):
    def __init__(self):
        super().__init__(image.create_transparent_surface((constant.SCREEN_WIDE, 100), color=image.TRANSPARENT), z=0)
        self._children = []
        # 创建用户栏
        self.user_bar = image.UIElement(image.load_image(constant.USERBAR_IMAGE_PATH),z=0)
        self.user_bar.set_center(constant.SCREEN_WIDE//2, 50)
        self._children.append(self.user_bar)

        self.user_icon = User(r'\B07.png',z = 1)
        self._children.append(self.user_icon)
    
    def draw(self, screen):
        self.image.fill(image.TRANSPARENT)
        for child in self._children:
            child.draw(self.image)
        super().draw(screen)

class Main(image.UIElement):
    def __init__(self):
        super().__init__(image.create_transparent_surface(constant.SCREEN_SIZE,color=image.TRANSPARENT), z=0)

        self._children = []
        # 创建用户栏
        self.user_bar = UserBar()
        self._children.append(self.user_bar)

        # 创建游戏开始按钮
        self.game_start_botton = Button("开始游戏", r'\B27.png', -210-105)
        self._children.append(self.game_start_botton)

        # 创建商店按钮
        self.store_botton = Button("商店", r'\B24.png', 105)
        self.store_botton.set_callback(self.store_click)
        self._children.append(self.store_botton)

    def handle_event(self, event, offset_x=0, offset_y=0):
        if not self.enabled or not self.visible:
            return False
        # 计算全局偏移
        global_off_x = offset_x + self.rect.x
        global_off_y = offset_y + self.rect.y
        for child in self._children:
            if child.handle_event(event, global_off_x, global_off_y):
                return True
        return False
    
    def store_click(self):
        self.change_to_store()

    def change_to_store(self):
        pass

    def draw(self, screen):
        # 绘制背景
        self.image=image.create_transparent_surface(constant.SCREEN_SIZE,color=image.TRANSPARENT)
        # 绘制按钮
        for child in self._children:
            child.draw(screen)
    

