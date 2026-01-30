#!/bin/bash

# --- 1. 网络与基础工具 ---
yay -S v2rayn-bin google-chrome

# --- 2 & 4. 安装 Fcitx5 与 RIME 雾凇小鹤版 ---
# 注意：rime-ice-double-pinyin-flypy-git 与 rime-ice-git 冲突
# 这里采用你指定的 flypy 专用版
sudo pacman -S --noconfirm fcitx5 fcitx5-gtk fcitx5-qt fcitx5-configtool fcitx5-rime
yay -S --noconfirm rime-ice-double-pinyin-flypy-git

# --- 3. 字体 ---
sudo pacman -S --noconfirm noto-fonts-cjk noto-fonts-emoji

# --- 5. 配置环境变量 ---
# 使用 echo 写入，避免使用 nano 手动编辑
echo "GTK_IM_MODULE DEFAULT=fcitx" >> /etc/environment
echo "QT_IM_MODULE  DEFAULT=fcitx" >> /etc/environment
echo "XMODIFIERS    DEFAULT=@im=fcitx" >> /etc/environment

# --- 7. 配置 RIME 输入法方案 ---
mkdir -p ~/.local/share/fcitx5/rime/

# 写入配置：启用小鹤双拼并包含雾凇词库建议
echo 'patch:
  schema_list:
    - schema: double_pinyin_flypy
  __include: rime_ice_suggestion:/' > ~/.local/share/fcitx5/rime/default.custom.yaml

# 建立必要的系统词库软链接（确保引擎能读到安装包里的词库）
ln -sf /usr/share/rime-data/rime_ice* ~/.local/share/fcitx5/rime/
ln -sf /usr/share/rime-data/cn_dicts ~/.local/share/fcitx5/rime/
ln -sf /usr/share/rime-data/en_dicts ~/.local/share/fcitx5/rime/
ln -sf /usr/share/rime-data/double_pinyin_flypy.schema.yaml ~/.local/share/fcitx5/rime/

# --- 8 & 10. 安装 Steam 与 NVIDIA 驱动组件 ---
yay -Syu --noconfirm steam vulkan-icd-loader nvidia-utils vulkan-tools \
    lib32-nvidia-utils lib32-vulkan-icd-loader nvidia-prime

# --- 9. 游戏性能工具 ---
yay -S --noconfirm proton-ge-custom-bin mangohud gamescope gamemode

# --- 12. 修改 sudo 超时时间 ---
# 推荐做法：在 sudoers.d 目录下创建独立配置文件，避免直接改动主文件
sudo bash -c 'echo "Defaults timestamp_timeout = 480" > /etc/sudoers.d/10-timeout'

echo "--------------------------------------------------"
echo "脚本执行完毕！请注销并重新登录以激活环境变量和输入法。"
echo "提醒：首次使用请在 Fcitx5 配置中手动添加 Rime 输入法。"
