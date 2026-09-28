# Linux 速查表（第 1 周）

> **纪律：这张表上的命令，用熟了就走，不要额外学。**
> 你需要的不是"学会 Linux"，是"能在 Linux 里不卡顿地干活"。

---

## 一、导航（用得最多）

```bash
pwd                     # 我在哪 (print working directory)
ls                      # 列出当前目录文件
ls -la                  # 列出全部（含隐藏文件）+ 详细信息
cd ~/projects           # 进入目录 (~ 代表你的家目录)
cd ..                   # 上一级
cd -                    # 回到上一个目录（来回跳很好用）
```

**记住 `~` 是什么**：`~` = `/home/你的用户名`。所以 `~/projects` = `/home/yun/projects`。

---

## 二、文件操作

```bash
mkdir 新目录名              # 建目录
mkdir -p a/b/c             # 建多层目录（-p 自动创建中间层）

cp 源文件 目标             # 复制文件
cp -r 源目录 目标目录      # 复制目录（-r = 递归）
mv 旧名 新名               # 重命名 / 移动

rm 文件名                  # 删文件
rm -rf 目录名              # 删目录【危险！删了进不了回收站】
```

> ⚠️ **`rm -rf` 是 Linux 上最危险的命令**。没有任何确认、没有回收站、删了就没了。
> **永远不要在 `rm -rf` 后面用 `~` 或 `/`**。敲之前先 `ls` 看一眼目标对不对。

---

## 三、看文件内容

```bash
cat 文件名                # 全部打印（小文件用）
less 文件名               # 分页查看（大文件用，q 退出，/关键词 搜索）
head -n 20 文件名         # 看前 20 行
tail -n 20 文件名         # 看后 20 行
tail -f 日志文件          # 实时跟踪文件新增内容【排错神器】
```

**`tail -f` 是你以后连板子时最常用的命令**——板子输出的日志会实时滚出来。

---

## 四、搜索

```bash
grep "关键词" 文件名              # 在文件里搜文本
grep -r "关键词" 目录/            # 递归搜索整个目录
grep -i "关键词" 文件             # 忽略大小写
grep -n "关键词" 文件             # 显示行号

find ~/projects -name "*.py"      # 按名字找文件
find . -name "*.jpg"              # 当前目录找所有 jpg
```

---

## 五、权限（会用到 sudo 就够了）

```bash
sudo 命令                 # 以管理员身份执行（会要密码）
sudo apt update           # 更新软件源
sudo apt install 包名     # 安装软件
chmod +x 脚本.sh          # 给文件加"可执行"权限
```

> **什么时候用 `sudo`？** 需要改系统文件、装系统软件时用。
> **普通写代码、pip install（在虚拟环境里）都不需要 sudo。**
> 乱用 sudo 是搞坏系统的头号原因。

---

## 六、系统状态

```bash
df -h                     # 磁盘剩余空间
free -h                   # 内存使用情况
top                       # 实时进程监控 (q 退出)
htop                      # 更好看的 top（需 sudo apt install htop）
ps aux                    # 列出所有进程
kill 进程号               # 结束进程
```

**以后板子上排查问题，`free -h` 和 `top` 是你最常用的两个。**

---

## 七、网络与远程（连板子会用到）

```bash
ip addr                   # 看本机 IP 地址
ping 目标地址             # 测试连通性
ssh 用户名@IP地址         # 远程登录另一台机器（以后连板子）
scp 文件 用户@IP:路径     # 远程复制文件
```

以后连香橙派的典型命令：

```bash
ssh orangepi@192.168.1.100        # 默认用户名密码通常都是 orangepi
scp model.rknn orangepi@192.168.1.100:~/
```

---

## 八、Python 与虚拟环境（天天用）

```bash
python3 --version                 # 看版本
python3 脚本.py                   # 运行脚本

python3 -m venv .venv             # 创建虚拟环境
source .venv/bin/activate         # 激活（每次开工第一件事）
deactivate                        # 退出虚拟环境

pip install 包名                  # 安装包
pip list                          # 看装了哪些包
pip freeze > requirements.txt     # 导出依赖清单
```

### 从零新建一个虚拟环境（Day 13 任务，5 步）

```bash
# ① 建目录并进去
mkdir -p ~/projects/test-venv
cd ~/projects/test-venv

# ② 创建虚拟环境（生成一个叫 .venv 的文件夹，几十 MB）
python3 -m venv .venv

# ③ 激活（命令行前面出现 (.venv) 就成功了）
source .venv/bin/activate

# ④ 装库（只会装进这个环境，系统 Python 一点不受影响）
pip install opencv-python

# ⑤ 验证 + 退出
python3 -c "import cv2; print(cv2.__version__)"
deactivate
```

**每一步在干什么**：

| 步 | 命令 | 说明 |
|---|---|---|
| ② | `python3 -m venv .venv` | 用当前 `python3` 造一份**独立的 Python 副本**放进 `.venv/` |
| ③ | `source .venv/bin/activate` | 把 `.venv/bin` 插到 PATH 最前面 → `python3`/`pip` 都变成这个环境的 |
| ④ | `pip install ...` | 装到 `.venv/lib/...`，**不污染系统 Python** |
| ⑤ | `deactivate` | 恢复成系统默认的 `python3`/`pip` |

**怎么确认自己在哪个环境**（随时可用）：

```bash
which python3                              # 应输出 .../test-venv/.venv/bin/python3
python3 -c "import sys; print(sys.prefix)" # 应输出 .../test-venv/.venv
pip -V                                     # 看 pip 属于哪个环境
echo $VIRTUAL_ENV                          # ★ 最直接：打印当前环境的绝对路径，没激活就是空
```

> **⚠️ 别在"已激活的环境"里再去激活另一个环境**
>
> 这是最容易混的一步：如果你在 `py-basics` 的 venv 还激活时，跑到另一个项目里建了新的 `.venv` 并激活它——
> **两个环境都叫 `.venv`，提示符长得一模一样 `(.venv)`，你根本分不清自己在哪个环境里。**
>
> 规范做法：**建新环境或切项目之前，先 `deactivate`**（或者干脆新开一个终端窗口）。
> 实在不确定时，永远用 `echo $VIRTUAL_ENV` 判一下——它永远不会骗你。
>
> 补充：在已激活的环境里执行 `python3 -m venv .venv`，Python 会正确地用**底层真实 Python** 去创建新环境（不会把两个环境串起来），所以不会弄坏东西，只是**容易让你自己看糊涂**。

**常见报错**：

| 报错 | 原因 | 解决 |
|---|---|---|
| `ensurepip is not available` | 缺 `python3-venv` | `sudo apt install -y python3-venv` |
| `Defaulting to user installation because normal site-packages is not writeable` | **没激活**，pip 跑去装系统了 | 重新 `source .venv/bin/activate` |
| 明明装了却 `ModuleNotFoundError: No module named 'cv2'` | 在 A 环境装的，在 B 环境用 | `which python3` 确认，重新激活 |
| pip 下载慢 | 没走镜像 | `~/.pip/pip.conf` 已配清华源会自动生效；临时指定：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple 包名` |

> **⚠️ venv 有一个硬限制：它不能换 Python 版本。**
> `python3 -m venv` 只能"复制当前这个 python3"。你系统里是 **3.14**，`.venv` 里也就是 3.14。
> 以后要建 **Python 3.10** 环境装 RKNN-Toolkit2 时，venv **做不到**，得用 conda：
> ```bash
> conda create -n rknn python=3.10 -y
> ```

> **虚拟环境就是一个文件夹**：`.venv/` 删掉 = 环境消失，随时能重建。所以放心试。

**以后每个新项目的标准开场**：

```bash
mkdir -p ~/projects/新项目名 && cd ~/projects/新项目名
python3 -m venv .venv && source .venv/bin/activate
pip install 需要的库
```

---

## 九、管道与重定向（理解了会很有用）

```bash
命令1 | 命令2             # 把命令1的输出给命令2处理
命令 > 文件               # 输出写到文件（覆盖）
命令 >> 文件              # 输出追加到文件

# 实用例子：
ls -la | grep ".py"              # 列出所有 py 文件
python3 train.py > log.txt 2>&1  # 训练日志存文件（2>&1 = 错误也一起存）
history | grep python            # 找我之前跑过的 python 命令
```

---

## 十、几个必须知道的操作技巧

| 操作 | 说明 |
|---|---|
| `Tab` 键 | **自动补全**——文件名和命令都能补全。少打字、少打错，用起来！ |
| `↑` / `↓` | 翻历史命令 |
| `Ctrl + C` | **中断当前运行的命令**（程序卡住/死循环时用） |
| `Ctrl + L` | 清屏（等于 `clear`） |
| `Ctrl + D` | 退出当前终端 |
| `Ctrl + A` / `Ctrl + E` | 光标跳到行首 / 行尾 |
| 命令前加 `\` | 例如 `\rm -rf`，加了转义就不会自动补全别名，能防手滑 |

---

## 十一、Windows 和 WSL 之间来回（互操作）

**核心认知：WSL 和 Windows 是两台"机器"**（只是共享剪贴板、网络和文件系统）。`explorer.exe` 是 Windows 程序，`ls` / `python3` 是 Linux 程序。**给 Windows 程序的路径，必须是 Windows 认得的路径。**

| 想干什么 | 在 Ubuntu 终端里敲 |
|---|---|
| 用资源管理器打开某个 Linux 目录 | `explorer.exe "$(wslpath -w ~/datasets/output)"` |
| 同上，先 cd 过去再开（`. ` 会被按当前目录翻译） | `cd ~/datasets/output && explorer.exe .` |
| 或者在 Windows 地址栏直接输入 | `\\wsl$\Ubuntu\home\user\datasets\output` |
| Linux 路径 → Windows 路径 | `wslpath -w ~/datasets/output` |
| Windows 路径 → Linux 路径 | `wslpath -u 'D:\嵌入式AI-车牌识别'` |
| 用 Windows 默认程序打开一个 Linux 文件 | `cmd.exe /c start 图片.jpg` |
| 在 Windows 里看 Linux 的 D 盘内容 | `ls /mnt/d/嵌入式AI-车牌识别` |

### 为什么 `explorer.exe ~/datasets/output` 跳不到目标目录？

`~` 是 **shell 的写法**，bash 先把它展开成 `/home/user/datasets/output`，然后把这条 **Linux 路径**交给了 Windows 程序。

Windows 只认 `C:\...` 或者 `\\wsl$\...` 这种形式，看到 `/home/...` 它解析不了，于是**打开默认位置（"此电脑"）**——看起来就像"没跳"。

**所以：路径带 `~` 或者以 `/` 开头，又要交给 `.exe` 程序，先用 `wslpath -w` 翻译一次。**

两个附带的小坑：

- `explorer.exe` **执行成功也返回退出码 1**（`echo $?` 是 1），别以为它失败了。
- 不想每次敲命令：把 `\\wsl$\Ubuntu\home\user\datasets\output` 在资源管理器里打开一次，右键 → **固定到"快速访问"**，以后一键直达。
- 反过来，Windows 里的项目目录 `D:\嵌入式AI-车牌识别\` 在 Linux 里就是 `/mnt/d/嵌入式AI-车牌识别/`，直接 `cd` 进去即可（只是**别在里面跑代码**，跨盘读写慢）。

---

## 第 1 周练习任务

**目标：把上面的命令用到不用想。**

1. **建目录结构**
   ```bash
   cd ~/projects
   mkdir -p linux-practice/{images,output,docs}
   cd linux-practice
   ```

2. **造几个文件**
   ```bash
   echo "第一行内容" > docs/note.txt
   echo "第二行内容" >> docs/note.txt
   cat docs/note.txt
   tail -n 1 docs/note.txt
   ```

3. **搜索**
   ```bash
   grep "第二行" docs/note.txt
   find . -name "*.txt"
   ```

4. **复制粘贴改名**
   ```bash
   cp docs/note.txt docs/note_backup.txt
   mv docs/note_backup.txt docs/note2.txt
   ls -la docs/
   ```

5. **看系统**
   ```bash
   df -h
   free -h
   top        # 然后按 q 退出
   ```

6. **删掉练习目录**（顺便练习谨慎用 rm）
   ```bash
   cd ~/projects
   ls              # 先确认你要删的是什么！
   rm -rf linux-practice
   ```

**全部敲一遍、没有报错，第 1 周就毕业了。**

---

## 每天记一条

在 `docs\踩坑记录.md` 里写下你今天遇到的问题和解决方式。

**这比任何笔记都有价值**——三个月后你会忘了自己踩过什么坑，而这份记录会救你。
