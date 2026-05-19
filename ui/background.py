import pygame
from ui import image
import constant


class Background(image.UIElement):
    def __init__(self):
        super().__init__(image.load_image(constant.BACKGROUND_IMAGE_PATH,size=constant.SCREEN_SIZE), z=-1)