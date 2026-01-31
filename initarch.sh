#!/bin/bash

# --- 1. 网络与基础工具 ---
# 增加 msr-tools 用于后续 CPU 解锁
# 增加 cpupower 用于实时监控和手动切换 CPU 调节器（Governor）
yay -S --noconfirm v2rayn-bin google-chrome msr-tools cpupower

# --- 2 & 4. 安装 Fcitx5 与 RIME 雾凇小鹤版 ---
sudo pacman -S --noconfirm fcitx5 fcitx5-gtk fcitx5-qt fcitx5-configtool fcitx5-rime
yay -S --noconfirm rime-ice-double-pinyin-flypy-git

# --- 3. 字体 ---
sudo pacman -S --noconfirm noto-fonts-cjk noto-fonts-emoji

# --- 5. 配置环境变量 ---
# 注意：使用 tee 确保权限正确，这里建议使用覆盖或检查避免重复写入
sudo bash -c 'cat <<EOF > /etc/environment
GTK_IM_MODULE=fcitx
QT_IM_MODULE=fcitx
XMODIFIERS=@im=fcitx
EOF'

# --- 7. 配置 RIME 输入法方案 ---
mkdir -p ~/.local/share/fcitx5/rime/

echo 'patch:
  schema_list:
    - schema: double_pinyin_flypy
  __include: rime_ice_suggestion:/' > ~/.local/share/fcitx5/rime/default.custom.yaml

ln -sf /usr/share/rime-data/rime_ice* ~/.local/share/fcitx5/rime/
ln -sf /usr/share/rime-data/cn_dicts ~/.local/share/fcitx5/rime/
ln -sf /usr/share/rime-data/en_dicts ~/.local/share/fcitx5/rime/
ln -sf /usr/share/rime-data/double_pinyin_flypy.schema.yaml ~/.local/share/fcitx5/rime/

# --- 8 & 10. 安装 Steam 与 NVIDIA 驱动组件 ---
# 增加 Intel 核显驱动补齐电源管理链条
# 增加 intel-compute-runtime 提供 OpenCL 支持，用于一些加速计算任务
yay -Syu --noconfirm steam vulkan-icd-loader nvidia-utils vulkan-tools \
    lib32-nvidia-utils lib32-vulkan-icd-loader nvidia-prime \
    intel-media-driver vulkan-intel libva-intel-driver intel-compute-runtime

# --- 9. 游戏性能工具 ---
yay -S --noconfirm proton-ge-custom-bin mangohud gamescope gamemode

# --- 12. 修改 sudo 超时时间 ---
sudo bash -c 'echo "Defaults timestamp_timeout = 480" > /etc/sudoers.d/10-timeout'

# --- 13. CPU 性能解锁 (针对 13650HX 锁频 2.6GHz 问题，个例问题勿用) ---
echo "正在配置 CPU 性能解锁服务..."

# 创建解锁服务文件
sudo bash -c 'cat <<EOF > /etc/systemd/system/unlock-cpu.service
[Unit]
Description=Unlock 13650HX Turbo and BDPROCHOT
After=multi-user.target suspend.target

[Service]
Type=oneshot
ExecStartPre=/usr/bin/modprobe msr
# 1. 关闭睿频限制
ExecStart=/usr/bin/bash -c "echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target suspend.target
EOF'

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable unlock-cpu.service
sudo systemctl start unlock-cpu.service

echo "--------------------------------------------------"
echo "脚本执行完毕！"
