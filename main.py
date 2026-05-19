'''
Author: NotechLogistics chenkai.32301@foxmail.com
Date: 2026-05-14 21:04:03
LastEditors: NotechLogistics chenkai.32301@foxmail.com
LastEditTime: 2026-05-19 15:21:14
FilePath: \homework\main.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import pygame
from ui import image
import os,sys



class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.running = True

    def run(self):        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            self.clock.tick(60)
            self.screen.fill(image.BLACK)
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main = Main()
    main.run()