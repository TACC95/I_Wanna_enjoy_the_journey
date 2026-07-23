import json
from pathlib import Path
import pygame
from classes.block import Sprite


class TiledMapLoader:
    """
    加载 Tiled 导出的 JSON 地图（.tmj）。

    使用方式：
        loader = TiledMapLoader('resources/tilesets/rooms/room_test/test_map_01.tmj')
        platforms = loader.load_layer('Tile Layer 1')
    """

    def __init__(self, map_path: str):
        """
        初始化地图加载器。

        参数:
            map_path: .tmj 地图文件的相对路径或绝对路径。
                      相对路径按当前工作目录解析。
        """
        self.map_path = Path(map_path).resolve()
        # 加载地图主文件
        self.map_data = self._load_json(self.map_path)

        # 基础信息
        self.tile_width = self.map_data['tilewidth']
        self.tile_height = self.map_data['tileheight']
        self.map_width = self.map_data['width']
        self.map_height = self.map_data['height']

        # 加载 tileset（地图引用的外部 tileset 文件）
        self.tileset = self._load_tileset()
        # 建立 tileset 里的 local_id -> block_id 映射
        self.tile_to_block = self._build_tile_to_block_mapping()

        # 加载方块注册表
        self.block_registry = self._load_block_registry()

        # 图片缓存，避免同一个贴图重复加载
        self._image_cache = {}

    def _load_json(self, path: Path) -> dict:
        """读取 JSON 文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_tileset(self) -> dict:
        """
        根据地图文件中的 source 路径，解析并加载外部 tileset。
        source 路径是相对于地图文件位置的。
        """
        # 取第一个 tileset（目前项目只用一个 tileset）
        tileset_info = self.map_data['tilesets'][0]
        tileset_source = tileset_info['source']

        # 从地图文件所在目录出发，解析 tileset 的相对路径
        tileset_path = self.map_path.parent / tileset_source
        tileset_path = tileset_path.resolve()

        return self._load_json(tileset_path)

    def _build_tile_to_block_mapping(self) -> dict:
        """
        遍历 tileset 中的每个 tile，读取其 block_id 自定义属性，
        建立 local_tile_id -> block_id 的映射。
        """
        mapping = {}
        for tile in self.tileset.get('tiles', []):
            local_id = tile['id']
            props = {p['name']: p['value'] for p in tile.get('properties', [])}
            if 'block_id' in props:
                # tileset 里 block_id 是字符串类型，转成 int
                mapping[local_id] = int(props['block_id'])
        return mapping

    def _load_block_registry(self) -> dict:
        """
        加载 data/block_registry.json，返回以 block_id（int）为 key 的字典。
        """
        registry_path = Path('./data/block_registry.json')
        data = self._load_json(registry_path)
        return {int(k): v for k, v in data['blocks'].items()}

    def _get_tile_image(self, tile: dict):
        """
        根据 tileset 中 tile 的 image 路径加载图片。
        image 路径是相对于 tileset 文件位置的。
        """
        image_path_relative = tile['image']

        # tileset 文件所在目录
        tileset_dir = (self.map_path.parent / self.map_data['tilesets'][0]['source']).parent
        image_path = (tileset_dir / image_path_relative).resolve()

        # 缓存：相同路径只加载一次
        path_str = str(image_path)
        if path_str not in self._image_cache:
            self._image_cache[path_str] = pygame.image.load(path_str).convert_alpha()

        return self._image_cache[path_str]

    def load_layer(self, layer_name: str = 'Tile Layer 1') -> pygame.sprite.Group:
        """
        加载指定名称的 tile layer，返回一个 Sprite 组。

        参数:
            layer_name: 要加载的图层名称，默认 "Tile Layer 1"
        """
        group = pygame.sprite.Group()

        for layer in self.map_data['layers']:
            # 只处理同名 tilelayer
            if layer.get('type') != 'tilelayer' or layer.get('name') != layer_name:
                continue

            layer_width = layer['width']
            layer_height = layer['height']

            for index, raw_gid in enumerate(layer['data']):
                # 0 表示空 tile
                if raw_gid == 0:
                    continue

                # Tiled 会把水平/垂直翻转、旋转信息编码到 gid 的高位。
                # 这里先去掉这些标志位，得到纯 tile ID。
                gid = raw_gid & 0x1FFFFFFF

                # 地图文件里的 gid 是全局 ID，需要减去 tileset 的 firstgid
                # 得到 tileset 内的 local_id
                firstgid = self.map_data['tilesets'][0]['firstgid']
                local_id = gid - firstgid

                # 查表得到 block_id
                block_id = self.tile_to_block.get(local_id)
                if block_id is None:
                    continue

                # 查注册表得到方块类型、贴图等信息
                block_info = self.block_registry.get(block_id)
                if block_info is None:
                    continue

                # 计算 tile 在地图中的像素坐标
                tile_x = (index % layer_width) * self.tile_width
                tile_y = (index // layer_width) * self.tile_height

                # 从 tileset 找到对应 tile，加载图片
                image = None
                for tile in self.tileset.get('tiles', []):
                    if tile['id'] == local_id:
                        image = self._get_tile_image(tile)
                        break

                # 创建方块精灵
                sprite = Sprite(
                    tile_x,
                    tile_y,
                    self.tile_width,
                    self.tile_height,
                    block_info['type'],
                    image
                )
                group.add(sprite)

            # 找到目标图层后就可以结束遍历
            break

        return group

    def load_object_layer(self, layer_name: str = 'Object Layer 1') -> list:
        """
        加载指定名称的对象层，返回对象列表。
        每个对象包含 x, y, width, height, name, properties 等。
        """
        for layer in self.map_data['layers']:
            if layer.get('type') == 'objectgroup' and layer.get('name') == layer_name:
                return layer.get('objects', [])
        return []

    def get_map_size(self) -> tuple:
        """返回地图总像素尺寸 (width, height)"""
        return (
            self.map_width * self.tile_width,
            self.map_height * self.tile_height
        )
