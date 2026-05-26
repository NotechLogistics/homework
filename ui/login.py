import pygame
from ui import image
import constant
from sql import mysql

class Login(image.UIElement):
    def __init__(self,db: mysql.MySQLHelper):
        super().__init__(image.create_transparent_surface(constant.SCREEN_SIZE,color=image.TRANSPARENT), z=0)
        self._children = []
        # 创建标题
        self.title = image.UIElement(image.load_image(constant.LOGIN_TITLE_IMAGE_PATH,size=constant.LOGIN_TITLE_IMAGE_SIZE),
                                     x=constant.SCREEN_SIZE[0]//2-constant.LOGIN_TITLE_IMAGE_WIDTH/2, y=150, z=1)
        self._children.append(self.title)
        # 创建登录表单
        self.form = image.FormPanel(
            x=150, y=100, panel_width=500,
            input_labels=["账号:", "密码:"],
            button_texts=["提交", "重置", "注册"],
            button_callbacks=[self.on_submit, self.on_cancel, self.on_register],
            label_font_size=22,
            input_font_size=20,
            input_height=35,
            row_gap=20,
            background_color=(*image.WHITE,128),
            border_color=image.BLUE,
            border_width=3,
            input_password_char="*",   # 密码框显示星号
            password_flags=[False, True],
            z=0
        )
        self.form.set_center(constant.SCREEN_WIDE//2, constant.SCREEN_HIGH//2 + 200)
        self._children.append(self.form)

        # 创建登录成功提示
        self.login_success = image.create_text("登录成功！", font_style="黑体", size=48, color=image.GREEN)
        self.login_success.set_center(constant.SCREEN_WIDE//2, self.form.rect.centery + 75)
        self.login_success.visible = False  # 初始隐藏成功提示
        self._children.append(self.login_success)

        # 创建登录失败提示
        self.login_fail = image.create_text("登录失败！", font_style="黑体", size=48, color=image.RED)
        self.login_fail.set_center(constant.SCREEN_WIDE//2, self.form.rect.centery + 75)
        self.login_fail.visible = False  # 初始隐藏失败提示
        self._children.append(self.login_fail)

        self.db = db

        self.change_to_register = None  # 切换到注册界面的回调函数
        self.change_to_main = None  # 切换到主界面的回调函数
        self.user_id = None
    def on_submit(self):
        values = self.form.get_input_values()
        account, password = values
        # 这里进行登录验证
        self.user_id = mysql.login_check(self.db, account, password)['user_id']
        if self.user_id:
            # 登录成功，切换到主界面
            self.login_success.visible = True  # 显示登录成功提示
            self.form.clear_inputs()  # 清空输入框
            self.form.enabled = False  # 禁用表单，防止重复提交
            for button in self.form.buttons:
                button.visible = False  # 隐藏按钮
            pygame.time.set_timer(pygame.USEREVENT + 1, 100)  # 设置2秒后触发USEREVENT+1事件
        else:
            # 登录失败，提示用户
            self.login_fail.visible = True  # 显示登录失败提示
            self.form.enabled = False
            for button in self.form.buttons:
                button.visible = False  # 隐藏按钮
            pygame.time.set_timer(pygame.USEREVENT + 2, 500)  # 设置2秒后触发USEREVENT+2事件

    def on_timer(self, event):
        if event.type == pygame.USEREVENT + 1:
            self.change_to_main()  # 切换回登录界面
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # 停止计时器
        if event.type == pygame.USEREVENT + 2:
            self.form.clear_inputs()  # 清空输入框
            self.form.enabled = True  # 重新启用表单
            for button in self.form.buttons:
                button.visible = True  # 显示按钮
            self.login_fail.visible = False  # 隐藏登录失败提示
            pygame.time.set_timer(pygame.USEREVENT + 2, 0)  # 停止定时器
        
    def on_cancel(self):
        self.form.clear_inputs()

    def on_register(self):
        self.change_to_register()

    def draw(self, screen, offset_x=0, offset_y=0):
        # 先清空自己的表面
        self.image.fill(image.TRANSPARENT)
        # 将所有子控件绘制到自己的表面上
        for child in self._children:
            child.draw(self.image)
        # 最后将自己的表面绘制到屏幕上
        screen.blit(self.image, (self.rect.x + offset_x, self.rect.y + offset_y))

    def handle_event(self, event, offset_x=0, offset_y=0):
        if not self.enabled or not self.visible:
            return False
        self.on_timer(event)  # 处理定时器事件
        # 计算全局偏移
        global_off_x = offset_x + self.rect.x
        global_off_y = offset_y + self.rect.y
        for child in self._children:
            if child.handle_event(event, global_off_x, global_off_y):
                return True
        return False