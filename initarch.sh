#!/bin/bash

set -e  # 遇到错误立即退出

echo "开始执行 EndeavourOS 快速部署脚本（针对 Intel 13650HX + RTX 4060）..."

# --- 0. 更新系统 & 确保 yay 可用（先跑一次完整更新） ---
sudo pacman -Syu --noconfirm
yay -Syu --noconfirm

# --- 1. CPU 微码（强烈推荐，防止 spectre/meltdown 等问题，重启生效） ---
sudo pacman -S --noconfirm intel-ucode

# --- 2. NVIDIA 驱动（推荐 open 内核模块，更稳定，尤其 Wayland） ---
# 注意：EndeavourOS 用 dracut，所以安装后必须重建 initramfs
# 如果想强制独显早加载（黑屏/wayland 问题），后面会创建 dracut conf
sudo pacman -S --noconfirm nvidia-open nvidia-utils lib32-nvidia-utils nvidia-prime
# 核显相关（游戏/视频硬解/日常省电）
sudo pacman -S --noconfirm mesa lib32-mesa vulkan-intel lib32-vulkan-intel intel-media-driver

# --- 3. 蓝牙 ---
sudo pacman -S --noconfirm bluez bluez-utils
sudo systemctl enable --now bluetooth

# --- 4. 安装 envycontrol（GPU 切换神器：integrated / hybrid / nvidia） ---
yay -S --noconfirm envycontrol

# --- 5. 重建 initramfs（必须！NVIDIA open 模块才能正确加载） ---
# EndeavourOS 默认 dracut，用 dracut-rebuild
# 如果你用 systemd-boot，还可以考虑 sudo reinstall-kernels（看你 bootloader）
sudo dracut-rebuild
# 可选：如果用 systemd-boot 且有 kernel 参数修改，再加这行
# sudo reinstall-kernels

# 强烈建议在这里重启一次测试驱动是否正常（nvidia-smi、prime-run glxinfo | grep NVIDIA）
echo "驱动安装完毕，建议现在重启一次测试（Ctrl+C 继续脚本）..."
# read -p "按 Enter 继续（或 Ctrl+C 退出）..."

# --- 6. 网络与基础工具 ---
yay -S --noconfirm v2rayn-bin google-chrome msr-tools cpupower

# --- 7. 安装 Fcitx5 + RIME 雾凇小鹤版 ---
sudo pacman -S --noconfirm fcitx5 fcitx5-gtk fcitx5-qt fcitx5-configtool fcitx5-rime
yay -S --noconfirm rime-ice-double-pinyin-flypy-git

# --- 8. 配置环境变量（KDE Wayland 最佳实践：只设 XMODIFIERS） ---
# 不要设 GTK/QT_IM_MODULE，否则候选框闪烁！
sudo bash -c 'cat <<EOF > /etc/environment
XMODIFIERS=@im=fcitx
# GTK_IM_MODULE=fcitx  # 注释掉或删除！Wayland 下会导致闪烁
# QT_IM_MODULE=fcitx   # 同上
EOF'

# 禁用 Fcitx5 系统级 autostart（防止 KWin 冲突报错）
sudo rm -f /etc/xdg/autostart/org.fcitx.Fcitx5.desktop || true
echo "已禁用 Fcitx5 系统 autostart。"

# --- 9. 配置 RIME（雾凇小鹤双拼） ---
RIME_DIR="$HOME/.local/share/fcitx5/rime"
mkdir -p "$RIME_DIR"

# 只启用 double_pinyin_flypy 方案
cat <<EOF > "$RIME_DIR/default.custom.yaml"
patch:
  schema_list:
    - schema: double_pinyin_flypy
EOF

# 符号链接雾凇核心文件（rime-ice 包提供）
ln -sf /usr/share/rime-data/rime_ice* "$RIME_DIR/" || true
ln -sf /usr/share/rime-data/cn_dicts "$RIME_DIR/" || true
ln -sf /usr/share/rime-data/en_dicts "$RIME_DIR/" || true
ln -sf /usr/share/rime-data/double_pinyin_flypy.schema.yaml "$RIME_DIR/" || true

# 清旧缓存
rm -rf "$RIME_DIR/build" || true

echo "RIME 配置完成！"
echo "重要步骤（必须手动做）："
echo "1. 注销/重启系统"
echo "2. 进入 System Settings → Input Devices → Virtual Keyboard（或 Keyboard → Virtual Keyboard）"
echo "3. 选择 'Fcitx 5'（不是 Fcitx5 Wayland Experimental，除非你测试）"
echo "4. 登录后，托盘出现 Fcitx5 图标 → 右键 RIME → Deploy（部署配置）"
echo "5. 在 Fcitx 配置中添加 RIME 输入法"
echo "如果 Chromium/Electron 应用输入有问题，加启动参数：--enable-features=UseOzonePlatform --ozone-platform=wayland --enable-wayland-ime"

# 可选：诊断工具（调试用）
# fcitx5-diagnose


# --- 10. Steam + 游戏相关（32位支持 + 性能工具） ---
yay -S --noconfirm steam vulkan-icd-loader lib32-vulkan-icd-loader \
    proton-ge-custom-bin mangohud gamescope gamemode intel-compute-runtime

# --- 11. 可选：NVIDIA dracut 强制加载模块（防黑屏/early KMS） ---
# 如果重启后有问题（如 wayland 黑屏），创建这个文件再 dracut-rebuild
sudo bash -c 'cat <<EOF > /etc/dracut.conf.d/nvidia.conf
force_drivers+=" nvidia nvidia_modeset nvidia_uvm nvidia_drm "
EOF'
# 然后再重建一次（可注释掉，如果第一次就正常就不需要）
# sudo dracut-rebuild

# --- 12. 修改 sudo 超时（480 分钟 = 8 小时） ---
sudo bash -c 'echo "Defaults timestamp_timeout = 480" > /etc/sudoers.d/10-timeout'

# --- 13. CPU 性能解锁（13650HX 锁频个例，慎用！测试后确认有效再启用） ---
# 注意：wrmsr 操作危险，建议先手动测试 msr-tools 是否可用
echo "配置 CPU 解锁服务（针对锁频/BDPROCHOT）..."
sudo bash -c 'cat <<EOF > /etc/systemd/system/unlock-cpu.service
[Unit]
Description=Unlock 13650HX Turbo and BDPROCHOT
After=multi-user.target
After=suspend.target

[Service]
Type=oneshot
ExecStartPre=/usr/bin/modprobe msr
ExecStart=/usr/bin/wrmsr 0x1FC 0xe8005e
ExecStartPost=/usr/bin/wrmsr 0x1a2 0x0c640000
ExecStartPost=/usr/bin/bash -c "echo 55000000 > /sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw"
ExecStartPost=/usr/bin/bash -c "echo 157000000 > /sys/class/powercap/intel-rapl:0/constraint_1_power_limit_uw"
ExecStartPost=/bin/echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target suspend.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable --now unlock-cpu.service

# --- 结束 ---
echo "脚本执行完毕！"
echo "强烈建议："
echo "1. 重启系统，让微码、NVIDIA、RIME 全部生效"
echo "2. 检查 nvidia-smi 是否正常"
echo "3. fcitx5 配置 → 添加 RIME 输入法 → 右键托盘图标 Deploy"
echo "4. envycontrol -s hybrid （推荐） 或 nvidia 模式，重启"
echo "如果有问题，运行 inxi -Fxxxz 贴出来排查。"
