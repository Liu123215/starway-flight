# 星轨穿梭 · Starway Flight

《星轨穿梭》是一款使用 Python 和 Tkinter 制作的 3D 太空飞行小游戏。驾驶飞船穿过 1,800 米的陨石航道，沿途收集能量晶体。飞船有 3 点机体耐久，撞上陨石扣 1 点，每颗晶体加 100 分。

Starway Flight is a 3D space arcade game built with Python and Tkinter. Steer through a 1,800 m asteroid course and collect energy crystals. You start with 3 hull points, lose 1 per hit, and earn 100 points per crystal.

## 安装与启动 / Install and run

登录有权限的 GitHub 账号，在仓库中选择 **Code → Download ZIP**，然后解压。游戏需要 Python 3.10 或更高版本和 Tcl/Tk。

Sign in with a GitHub account that can access the repository. Choose **Code → Download ZIP** and extract it. The game requires Python 3.10 or later with Tcl/Tk.

### Windows

安装支持 Tcl/Tk 的 Windows 版 Python。解压后双击 `run_game.bat`，或在项目目录运行下面的命令。Windows 上已实测游戏和合成音效的播放调用。 [Python Windows 下载](https://www.python.org/downloads/windows/)

Install Python for Windows with Tcl/Tk support. Double-click `run_game.bat`, or run the command below from the extracted folder. The game and sound playback calls were tested on Windows. [Python for Windows](https://www.python.org/downloads/windows/)

```powershell
py -3 main.py
```

### Linux

在图形桌面中选择适合你的发行版的命令，安装 Python 和 Tkinter。然后在解压后的项目目录运行 `python3 main.py`。 [Ubuntu](https://packages.ubuntu.com/search?keywords=python3-tk) · [Debian](https://packages.debian.org/trixie/python3-tk) · [Fedora](https://packages.fedoraproject.org/pkgs/python3.14/python3-tkinter/) · [Arch Linux](https://archlinux.org/packages/core/x86_64/python/)

In a graphical desktop session, install Python and Tkinter using the commands for your distribution. Then run `python3 main.py` from the extracted folder.

```sh
# Ubuntu / Debian
sudo apt update
sudo apt install python3 python3-tk

# Fedora
sudo dnf install python3 python3-tkinter

# Arch Linux
sudo pacman -S --needed python tk
```

### Android · Termux + Termux:X11

1. 在 Android 7 或更高版本上安装 Termux 和 Termux:X11 通用版 APK。 / On Android 7 or later, install Termux and the universal Termux:X11 APK. [Termux 安装说明 / Termux installation](https://github.com/termux/termux-app#installation) · [Termux:X11 APK](https://github.com/termux/termux-x11/releases/tag/nightly)
2. 把 ZIP 在系统的 **Download** 目录解压。在 Termux 中运行以下命令。提示访问存储时，允许 Termux 读取解压后的项目。 / Extract the ZIP into the system **Download** folder. Run the following commands in Termux and grant storage access to read the project when prompted.

   ```sh
   pkg update
   pkg install x11-repo
   pkg install python python-tkinter termux-x11-nightly
   termux-setup-storage
   ```

3. 允许访问存储后，在 Termux 中启动游戏。若解压出来的文件夹名不同，请用实际名称。 / After granting storage access, start the game in Termux. If the extracted folder has a different name, use that name in the path.

   ```sh
   cd ~/storage/downloads/starway-flight-main && termux-x11 :1 -- python -B main.py
   ```

4. 切换到 Termux:X11 查看游戏窗口。建议横屏，X11 分辨率至少为 800×520，接实体键盘控制飞船。如果显示器 `:1` 已经在运行，在项目目录执行 `DISPLAY=:1 python -B main.py`。 / Switch to Termux:X11 to view the game. Use landscape mode, an X11 resolution of at least 800×520, and a physical keyboard to steer. If display `:1` is already running, use `DISPLAY=:1 python -B main.py` in the project folder. [Termux:X11 运行说明 / Termux:X11 setup](https://github.com/termux/termux-x11#running-graphical-applications)

Linux 与 Android 的步骤依据上游安装文档整理。检查 Tkinter 时，Linux 图形桌面可运行 `python3 -m tkinter`，Android 可在 X11 显示器启动后运行 `DISPLAY=:1 python -m tkinter`。游戏音效使用 Windows 音频接口。 / The Linux and Android steps follow upstream installation guidance. To check Tkinter, run `python3 -m tkinter` on a Linux desktop or `DISPLAY=:1 python -m tkinter` once the Android X11 display is running. Game audio uses the Windows sound API. [Tkinter 文档 / Tkinter documentation](https://docs.python.org/3/library/tkinter.html)

## 操作 / Controls

| 按键 / Key | 中文 | English |
| --- | --- | --- |
| `WASD` / 方向键 · Arrow keys | 移动飞船 | Steer the ship |
| `P` / `Esc` | 暂停或继续 | Pause or resume |
| `Enter` | 开始、继续或再玩一局 | Start, resume, or play again |
| `R` | 在结算画面再玩一局 | Play again from the results screen |
| `M` | 开关音效 | Toggle sound |
| `L` | 切换界面语言 | Switch languages |

右下角也可切换语言。最高分、语言和静音设置保存在本机。 / The language button is also available in the lower-right corner. Your best score, language, and mute setting are stored locally.
