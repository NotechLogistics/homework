import pygame
from ui import image,ui_manager,background
import os,sys
import constant

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(constant.SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True

        # 创建ui管理器
        self.ui_manager = ui_manager.UIManager()

        # 创建背景
        self.background = background.Background()
        self.ui_manager.add(self.background)  # 将背景图片添加到UI管理器中

        # 创建普通输入框
        name_input = image.InputBox(
            x=100, y=100, width=250, height=40,
            placeholder="请输入姓名",
            max_length=20,
            z=1
        )
        # 创建密码输入框
        pwd_input = image.InputBox(
            x=100, y=160, width=250, height=40,
            placeholder="密码",
            password_char="*",
            max_length=16,
            z=1
        )
        # 数字输入框
        age_input = image.InputBox(
            x=100, y=220, width=100, height=40,
            placeholder="年龄",
            allowed_chars="0123456789",
            max_length=3,
            z=1
        )

        self.ui_manager.add(name_input)
        self.ui_manager.add(pwd_input)
        self.ui_manager.add(age_input)

    def run(self):
        dt = self.clock.tick(60) / 1000.0    
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.ui_manager.handle_event(event)
            self.clock.tick(60)

            for elem in self.ui_manager.elements:
                if isinstance(elem, image.InputBox):
                    elem.update(dt)

            self.screen.fill(image.BLACK)
            self.ui_manager.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main = Main()
    main.run()