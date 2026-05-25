import pygame
from ui import image
import constant


class Login(image.UIElement):
    def __init__(self):
        super().__init__(image.create_transparent_surface(constant.SCREEN_SIZE,color=image.TRANSPARENT), z=0)
        
        self.title = image.UIElement(image.load_image(constant.LOGIN_TITLE_IMAGE_PATH,size=constant.LOGIN_TITLE_IMAGE_SIZE),
                                     x=constant.SCREEN_SIZE[0]//2-constant.LOGIN_TITLE_IMAGE_WIDTH/2, y=150, z=1)
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
        self._children = [self.title, self.form]
        self.change_to_register = None  # 切换到注册界面的回调函数
        self.change_to_main = None  # 切换到主界面的回调函数
    def on_submit(self):
        values = self.form.get_input_values()
        account, password = values
        print(f"提交登录: 账号={account}, 密码={password}")
        # 这里进行登录验证
        pass
        # 假设成功
        self.change_to_main()
    def on_cancel(self):
        self.form.clear_inputs()
        print("取消登录")
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
        # 计算全局偏移
        global_off_x = offset_x + self.rect.x
        global_off_y = offset_y + self.rect.y
        for child in self._children:
            if child.handle_event(event, global_off_x, global_off_y):
                return True
        return False