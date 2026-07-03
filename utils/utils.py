import os
import pygame

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')


def load_images(subfolder):
    """加载指定子文件夹下的所有 PNG 图片，按文件名排序"""
    folder = os.path.join(RESOURCES_DIR, subfolder)
    images = []
    for filename in sorted(os.listdir(folder)):
        if filename.endswith('.png'):
            img = pygame.image.load(os.path.join(folder, filename)).convert_alpha()
            images.append(img)
    return images


def load_image(subfolder, filename):
    """加载单个图片文件"""
    path = os.path.join(RESOURCES_DIR, subfolder, filename)
    return pygame.image.load(path).convert_alpha()