"""
快速注册新方块到 data/block_registry.json

用法：
    python tools/register_block.py

会交互式询问方块信息，自动分配最小可用 ID。
"""

import json
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / 'data' / 'block_registry.json'


def load_registry():
    """加载已有注册表，如果不存在返回空结构"""
    if not REGISTRY_PATH.exists():
        return {'blocks': {}}
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_registry(registry):
    """保存注册表到 JSON 文件"""
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write('\n')


def get_next_id(registry):
    """获取最小的未使用正整数 ID"""
    existing_ids = {int(k) for k in registry['blocks'].keys()}
    new_id = 1
    while new_id in existing_ids:
        new_id += 1
    return new_id


def main():
    registry = load_registry()

    print('=== 方块注册工具 ===')
    print(f'注册表路径: {REGISTRY_PATH.relative_to(PROJECT_ROOT)}')
    print(f'当前已有 {len(registry["blocks"])} 个方块')
    print()

    # 询问方块信息
    name = input('方块名称（如 floor_2）: ').strip()
    if not name:
        print('名称不能为空')
        sys.exit(1)

    # 检查名称是否已存在
    for bid, info in registry['blocks'].items():
        if info.get('name') == name:
            print(f'错误：名称 "{name}" 已被 ID {bid} 使用')
            sys.exit(1)

    block_type = input('方块类型（solid/spike/bg/save/goal/trigger）: ').strip()
    if not block_type:
        print('类型不能为空')
        sys.exit(1)

    file_path = input('贴图相对路径（无贴图则留空）: ').strip()
    if file_path == '':
        file_path = None

    # 自动分配 ID
    new_id = get_next_id(registry)

    # 写入注册表
    registry['blocks'][str(new_id)] = {
        'name': name,
        'type': block_type,
        'file': file_path
    }

    save_registry(registry)

    print()
    print(f'已注册方块：')
    print(f'  ID: {new_id}')
    print(f'  名称: {name}')
    print(f'  类型: {block_type}')
    print(f'  贴图: {file_path}')
    print(f'请记得在 Tiled tileset 里给对应 tile 添加属性 block_id = {new_id}')


if __name__ == '__main__':
    main()
