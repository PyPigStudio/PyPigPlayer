import pygame


class Button():
    def __init__(self, id):
        self.id = id
        self.img = None

    def show(self, screen, pos, size):
        if self.img:
            img = pygame.transform.scale(self.img, (int(size),)*2)
            self.rect = img.get_rect()
            self.rect.center = pos
            screen.blit(img, self.rect)

    def set_img(self, img):
        if img:
            self.img = pygame.image.load(f'img/{img}.png')
        else:
            self.img = None

    def test_click(self, pos):
        if self.rect.collidepoint(pos):
            self.onclick()
