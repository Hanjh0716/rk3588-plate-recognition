# 练习目录

这个目录里的内容会在你跑 `setup\2-配置Python环境.bat` 时，**自动复制到 WSL 的 `~/projects/practice/`**。

## 目录说明

```
practice/
├── 01-linux/      ← 第1周：Linux 命令练习（对应 docs/02-Linux速查表.md）
└── 02-python/     ← 第2-3周：Python 14天练习（对应 docs/03-Python练习计划.md）
```

## 为什么代码不能放在这里写

这个目录在 **Windows 的 D 盘**上。WSL 访问 Windows 文件走的是 `/mnt/d/` 路径，**跨文件系统读写有严重性能损失**。

所以：

| 用途 | 位置 |
|---|---|
| ✅ 写代码、跑程序 | `~/projects/` （WSL 内部） |
| ✅ 存图片、数据集 | `~/datasets/` （WSL 内部） |
| ⚠️ 大文件、备份、教程 | D 盘（放这里没问题） |

**规则：代码一律在 WSL 内部写。** 这个目录只作为模板源和备份。

## 正确的开工方式

```bash
cd ~/projects/py-basics
source .venv/bin/activate
code .
```

然后就在 VS Code 里开始写当天的练习。
