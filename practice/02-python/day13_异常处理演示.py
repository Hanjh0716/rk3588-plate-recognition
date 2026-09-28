# ============================================================
# Day 13 配套演示：异常处理是怎么回事
# ============================================================
# 用法:
#     cd ~/projects/py-basics && source .venv/bin/activate
#     python3 day13_异常处理演示.py
#
# 特点: 不需要图片、不需要 opencv，直接跑就能看到每一步输出
# 讲解: docs/08-异常处理.md
# ============================================================


def sec(title):
    print()
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)


# ------------------------------------------------------------
sec("1. 异常是什么：没人接住，程序就当场死")
print("如果直接写 1/0，Python 会抛 ZeroDivisionError，脚本立刻中断、后面全不执行。")
print("这里用 try 接住它，只是为了让你能继续往下看：")
try:
    1 / 0
except Exception as e:
    print(f"  接住了 -> {type(e).__name__}: {e}")
    print(f"  类型名: {type(e).__name__}   消息: {e}")


# ------------------------------------------------------------
sec("2. try / except：出错就跳走，中间代码全部跳过")
try:
    print("  [try]    第一行，正常执行")
    raise ValueError("我故意抛的")
    print("  [try]    这一行永远不会执行（因为上面 raise 了）")
except Exception as e:
    print(f"  [except] 接住: {type(e).__name__}: {e}")
print("  循环/函数继续往下走 —— 这就是'不崩'")


# ------------------------------------------------------------
sec("3. else 和 finally 什么时候执行")


def demo(should_fail):
    try:
        if should_fail:
            raise RuntimeError("故意失败")
    except RuntimeError as e:
        print(f"    except : {e}")
    else:
        print("    else   : 只有没出错才执行")
    finally:
        print("    finally: 无论成功失败都执行（收尾用）")


print("  情况 A —— 失败：")
demo(True)
print("  情况 B —— 成功：")
demo(False)


# ------------------------------------------------------------
sec("4. 常见异常类型（逐个触发，顺便记住名字）")

cases = [
    ("值不对      ", lambda: int("abc")),
    ("类型不对    ", lambda: "a" + 1),
    ("变量没定义  ", lambda: eval("undefined_name_xyz")),
    ("列表越界    ", lambda: [1, 2, 3][99]),
    ("字典没有这个键", lambda: {"a": 1}["b"]),
    ("除以零      ", lambda: 1 / 0),
    ("None 取属性 ", lambda: None.shape),
    ("文件不存在  ", lambda: open("/tmp/这个文件肯定不存在_abc123.txt")),
    ("模块不存在  ", lambda: __import__("no_such_module_abc123")),
]

for desc, fn in cases:
    try:
        fn()
        print(f"  {desc} -> 居然没出错？")
    except Exception as e:
        print(f"  {desc} -> {type(e).__name__}: {e}")

print()
print("  另外两个不在 Exception 里的：")
print("    KeyboardInterrupt —— 你按 Ctrl+C（所以裸 except: 会把它一起吞掉）")
print("    SystemExit        —— raise SystemExit() / sys.exit()")


# ------------------------------------------------------------
sec("5. raise：把'安静的失败'主动升级成异常")
print("场景：函数用**返回值**表示失败，而不是抛异常（OpenCV 就是这样）")


def fake_imread(path):
    return None            # 模拟：文件损坏，读不出来


print()
print("  做法 A —— 不管它，直接往下用：")
img = fake_imread("broken.jpg")
print(f"    img = {img}")
try:
    print(img.shape)       # None 没有 shape
except AttributeError as e:
    print(f"    -> {type(e).__name__}: {e}")
    print("       （你之前 imshow 报 'size.width>0' 断言失败，根子就是这个）")

print()
print("  做法 B —— 第一时间 raise，让它走统一的 except 通道：")
try:
    img = fake_imread("broken.jpg")
    if img is None:
        raise ValueError("imread 返回 None（文件损坏 / 不是图片）")
    print(img.shape)       # 这行不会执行
except Exception as e:
    print(f"    接住 -> {type(e).__name__}: {e}")
    print("    好处：后面 resize / rectangle 全部跳过，不会崩得莫名其妙")


# ------------------------------------------------------------
sec("6. 完整骨架：批量处理时怎么'记账'")

fake_files = ["a.jpg", "broken.jpg", "c.jpg"]


def fake_process(name):
    if name == "broken.jpg":
        return None                     # 模拟读图失败
    return {"name": name, "shape": (480, 640, 3)}


ok_list, fail_list = [], []
total = len(fake_files)

for index, name in enumerate(fake_files, start=1):
    try:
        result = fake_process(name)
        if result is None:
            raise ValueError("imread 返回 None")
        ok_list.append(name)
        print(f"  [{index}/{total}] 成功: {name}")
    except Exception as e:
        fail_list.append((name, f"{type(e).__name__}: {e}"))
        print(f"  [{index}/{total}] 失败: {name} -> {type(e).__name__}: {e}")

print()
print(f"  共 {total} 张：成功 {len(ok_list)}，失败 {len(fail_list)}")
for name, reason in fail_list:
    print(f"    ✗ {name}: {reason}")
print()
print("  注意 fail_list 里存的是元组 (文件名, 原因)，所以最后能一次拆成两个值")


# ------------------------------------------------------------
sec("7. 三个必须记住的结论")
print("  ① 安静的失败（None / False / 空列表）用 if 判断，try/except 抓不住")
print("  ② 抛出的异常用 try/except 接，接住后一定要记录 e，不要 pass")
print("  ③ try 的范围要小：只包可能出事的那几行（批量处理里'整张图'算一个单元）")
print()
print("  两道防线合起来才叫'错误处理'：")
print("     if img is None: raise ...   ← 第一道：抓安静的失败")
print("     except Exception as e: ...  ← 第二道：抓所有异常")
print()
print("演示结束。现在去看 docs/08-异常处理.md，对照着理解 day13.py。")
