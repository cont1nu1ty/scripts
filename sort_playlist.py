#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歌单排序工具 - 支持 .lxmc 格式
根据文本文件中的歌曲顺序，对 lx_list.lxmc 文件中的歌单进行排序

完整流程：
1. 解压 lx_list.lxmc (gzip) → lx_list (JSON)
2. 读取并排序歌单
3. 保存 lx_list (JSON)
4. 压缩 lx_list → lx_list.lxmc (gzip)
5. 清理临时文件

使用方法：
    python sort_playlist.py [歌曲列表文件] [歌单名称]
    
示例：
    python sort_playlist.py 121.txt 1
    python sort_playlist.py order.txt "我的歌单"
    
默认参数：
    歌曲列表: 121.txt
    歌单名称: 1
"""

import json
import sys
import os
import re
import gzip
import shutil


def parse_song_list(file_path):
    """
    解析歌曲列表文件
    格式示例：
        Smooth Criminal
        David Garrett
        03:07
        
        Alone
           Alan Walker
           02:41
    """
    songs = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"✗ 错误: 找不到文件 '{file_path}'")
        sys.exit(1)
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过空行
        if not line:
            i += 1
            continue
        
        # 跳过纯时间格式的行（如 03:07）
        if re.match(r'^\d{1,2}:\d{2}$', line):
            i += 1
            continue
        
        # 第一行是歌名
        song_name = line
        
        # 查找下一个非空行作为艺术家名
        artist_name = ""
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if next_line:
                # 如果是时间格式，说明没有艺术家信息
                if re.match(r'^\d{1,2}:\d{2}$', next_line):
                    i += 1
                    break
                else:
                    artist_name = next_line
                    i += 1
                    # 跳过时间行
                    if i < len(lines):
                        time_line = lines[i].strip()
                        if re.match(r'^\d{1,2}:\d{2}$', time_line):
                            i += 1
                    break
            i += 1
        
        songs.append({
            'name': song_name,
            'artist': artist_name
        })
    
    return songs


def normalize_text(text):
    """标准化文本用于比较"""
    if not text:
        return ""
    # 移除括号及其内容
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = re.sub(r'【[^】]*】', '', text)
    # 移除特殊字符和空格
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
    return text.lower()


def match_song(song_info, playlist_songs):
    """
    在歌单中匹配歌曲
    song_info: {'name': '歌名', 'artist': '艺术家'}
    playlist_songs: lx_list 中的歌曲列表
    
    返回: (匹配的歌曲, 匹配得分)
    """
    target_name = normalize_text(song_info['name'])
    target_artist = normalize_text(song_info['artist'])
    
    best_match = None
    best_score = 0
    
    for song in playlist_songs:
        song_name = normalize_text(song.get('name', ''))
        song_singer = normalize_text(song.get('singer', ''))
        
        score = 0
        
        # 完全匹配歌名
        if target_name and song_name and target_name == song_name:
            score = 100
            # 艺术家也匹配，大幅加分
            if target_artist and (target_artist in song_singer or song_singer in target_artist):
                score = 200
        # 歌名包含关系（模糊匹配）
        elif target_name and song_name:
            if target_name in song_name:
                # 目标名称在歌曲名中
                overlap_ratio = len(target_name) / len(song_name)
                score = 60 * overlap_ratio
            elif song_name in target_name:
                # 歌曲名在目标名称中
                overlap_ratio = len(song_name) / len(target_name)
                score = 50 * overlap_ratio
            
            # 艺术家匹配加分
            if score > 0 and target_artist and (target_artist in song_singer or song_singer in target_artist):
                score += 30
        
        if score > best_score:
            best_score = score
            best_match = song
    
    # 只有得分超过阈值才返回匹配结果
    if best_score >= 50:
        return best_match
    
    return None


def find_playlist_by_name(data, playlist_name):
    """根据歌单名称查找歌单"""
    for playlist in data['data']:
        if playlist.get('name') == playlist_name:
            return playlist
    return None


def decompress_lxmc(lxmc_file, output_file):
    """解压 .lxmc 文件"""
    try:
        with gzip.open(lxmc_file, 'rb') as f_in:
            with open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return True
    except Exception as e:
        print(f"      ✗ 解压失败: {e}")
        return False


def compress_lxmc(input_file, lxmc_file):
    """压缩为 .lxmc 文件"""
    try:
        with open(input_file, 'rb') as f_in:
            with gzip.open(lxmc_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return True
    except Exception as e:
        print(f"      ✗ 压缩失败: {e}")
        return False


def sort_playlist(order_file, lxmc_file, playlist_name='1'):
    """主排序函数"""
    
    print("=" * 70)
    print(" " * 25 + "歌单排序工具")
    print("=" * 70)
    
    # 文件路径
    temp_file = lxmc_file[:-5] if lxmc_file.endswith('.lxmc') else lxmc_file
    backup_file = lxmc_file + '.backup'
    
    # 1. 解压 .lxmc 文件
    print(f"\n[1/6] 解压文件")
    print(f"      输入: {lxmc_file}")
    print(f"      输出: {temp_file}")
    
    if not os.path.exists(lxmc_file):
        print(f"      ✗ 错误: 找不到文件 '{lxmc_file}'")
        sys.exit(1)
    
    if decompress_lxmc(lxmc_file, temp_file):
        print(f"      ✓ 解压成功")
    else:
        sys.exit(1)
    
    # 2. 读取歌曲顺序列表
    print(f"\n[2/6] 读取歌曲列表")
    print(f"      文件: {order_file}")
    order_songs = parse_song_list(order_file)
    print(f"      ✓ 成功读取 {len(order_songs)} 首歌曲")
    
    # 3. 读取 JSON 数据
    print(f"\n[3/6] 读取歌单数据")
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"      ✓ 成功读取文件")
    except FileNotFoundError:
        print(f"      ✗ 错误: 找不到文件 '{temp_file}'")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"      ✗ 错误: JSON 格式错误 - {e}")
        sys.exit(1)
    
    # 4. 找到目标歌单并排序
    print(f"\n[4/6] 查找并排序歌单")
    print(f"      歌单名称: {playlist_name}")
    
    playlist = find_playlist_by_name(data, playlist_name)
    
    if not playlist:
        print(f"      ✗ 错误: 未找到名称为 '{playlist_name}' 的歌单")
        print(f"\n可用的歌单:")
        for p in data['data']:
            print(f"  - 名称: {p.get('name')}, ID: {p.get('id')}, 歌曲数: {len(p.get('list', []))}")
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
        sys.exit(1)
    
    original_songs = playlist['list']
    print(f"      ✓ 找到歌单，共 {len(original_songs)} 首歌曲")
    print(f"\n      开始匹配...")
    
    new_list = []
    matched_ids = set()
    matched_count = 0
    not_found = []
    
    for idx, song_info in enumerate(order_songs, 1):
        matched_song = match_song(song_info, original_songs)
        
        if matched_song:
            song_id = matched_song['id']
            if song_id not in matched_ids:
                new_list.append(matched_song)
                matched_ids.add(song_id)
                matched_count += 1
                # 显示匹配结果
                matched_name = matched_song.get('name', 'Unknown')
                if len(matched_name) > 40:
                    matched_name = matched_name[:37] + '...'
                print(f"      [{idx:2d}] ✓ {song_info['name'][:35]}")
            else:
                print(f"      [{idx:2d}] ⊘ 重复: {song_info['name'][:35]}")
        else:
            not_found.append(song_info)
            print(f"      [{idx:2d}] ✗ 未找到: {song_info['name'][:35]}")
    
    # 添加剩余歌曲（保持原顺序）
    remaining = []
    for song in original_songs:
        if song['id'] not in matched_ids:
            remaining.append(song)
    
    new_list.extend(remaining)
    
    # 更新歌单
    playlist['list'] = new_list
    
    # 统计信息
    print(f"\n      " + "=" * 60)
    print(f"      排序统计:")
    print(f"        ✓ 成功匹配: {matched_count} 首")
    print(f"        ✗ 未找到:   {len(not_found)} 首")
    print(f"        + 未排序:   {len(remaining)} 首 (追加到末尾)")
    print(f"        = 总计:     {len(new_list)} 首")
    
    if not_found:
        print(f"\n      未找到的歌曲 (不在歌单中):")
        for i, song in enumerate(not_found[:5], 1):
            print(f"        {i}. {song['name']} - {song['artist']}")
        if len(not_found) > 5:
            print(f"        ... 还有 {len(not_found) - 5} 首")
    
    # 5. 保存 JSON 文件
    print(f"\n[5/6] 保存JSON文件")
    print(f"      文件: {temp_file}")
    
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"      ✓ 保存成功")
    except Exception as e:
        print(f"      ✗ 保存失败: {e}")
        sys.exit(1)
    
    # 6. 压缩为 .lxmc 文件
    print(f"\n[6/6] 压缩文件")
    
    # 创建备份
    if os.path.exists(lxmc_file):
        try:
            shutil.copy2(lxmc_file, backup_file)
            print(f"      ✓ 已创建备份: {backup_file}")
        except Exception as e:
            print(f"      ⚠ 备份失败: {e}")
    
    print(f"      正在压缩...")
    if compress_lxmc(temp_file, lxmc_file):
        print(f"      ✓ 压缩成功: {lxmc_file}")
    else:
        sys.exit(1)
    
    # 清理临时文件
    try:
        os.remove(temp_file)
        print(f"      ✓ 已清理临时文件: {temp_file}")
    except:
        pass
    
    print("=" * 70)
    print(" " * 28 + "✓ 全部完成！")
    print("=" * 70)


def main():
    """主函数"""
    
    # 默认参数
    order_file = input("请输入 排序txt文件： xxx.txt").strip()    
    lxmc_file = 'lx_list.lxmc'
    playlist_name = input("请输入 playlist_name: ").strip()
    
    # 解析命令行参数
    if len(sys.argv) >= 2:
        order_file = sys.argv[1]
    if len(sys.argv) >= 3:
        playlist_name = sys.argv[2]
    
    # 显示使用的参数
    print(f"\n使用参数:")
    print(f"  歌曲列表: {order_file}")
    print(f"  歌单文件: {lxmc_file}")
    print(f"  歌单名称: {playlist_name}")
    
    # 执行排序
    sort_playlist(order_file, lxmc_file, playlist_name)


if __name__ == '__main__':
    main()