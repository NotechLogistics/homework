import pygame
from ui import image,ui_manager,background,login,register,main
import os,sys
import constant
import sql.mysql

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(constant.SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.status = 'login'  # 当前状态，初始为登录界面
        self.user_id = None  # 当前登录用户的ID
        self.db = sql.mysql.MySQLHelper(
            host=constant.MYSQL_HOST,
            port=constant.MYSQL_PORT,
            user=constant.MYSQL_USER,
            password=constant.MYSQL_PASSWORD,
            database=constant.MYSQL_DATABASE,
        )  # 创建MySQL实例

        # 创建ui管理器
        self.ui_manager = ui_manager.UIManager()

        # 创建背景
        self.background = background.Background()
        self.ui_manager.add(self.background)  # 将背景图片添加到UI管理器中
        
        # 创建登录界面
        self.login = login.Login(self.db)
        self.login.change_to_register = self.change_to_register  # 设置注册按钮的回调函数
        self.login.change_to_main = self.change_to_main  # 设置登录成功后切换到主界面的回调函数

        # 创建注册界面
        self.register = register.Register(self.db)  # 注册界面实例，初始为None
        self.register.change_to_login = self.change_to_login  # 设置注册界面中切换回登录界面的回调函数

        # 创建主界面
        self.main = main.Main()
        self.main.change_to_store = self.change_to_store
        
    def run(self):
        dt = self.clock.tick(60) / 1000.0    
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.ui_manager.handle_event(event)
            self.clock.tick(60)

            if self.status == 'login':
                if self.login not in self.ui_manager.elements:
                    self.ui_manager.add(self.login)
            if self.status == 'register':
                if self.register not in self.ui_manager.elements:
                    self.ui_manager.add(self.register)
            if self.status == 'main':
                if self.main not in self.ui_manager.elements:
                    self.ui_manager.add(self.main)
            self.ui_manager.update(dt)
            self.ui_manager.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def change_to_register(self):
        self.status = 'register'

        self.ui_manager.elements.remove(self.login)  # 从UI管理器中移除登录界面
    def change_to_main(self):
        self.status = 'main'
        self.user_id = self.login.user_id
        self.ui_manager.elements.remove(self.login) # 从UI管理器中移除登录界面`
    def change_to_login(self):
        self.status = 'login'

        self.ui_manager.elements.remove(self.register)  # 从UI管理器中移除注册界面
    def change_to_store(self):
        self.status = 'store'

        print("切换到商店界面")


if __name__ == "__main__":
    main = Main()
    main.run()