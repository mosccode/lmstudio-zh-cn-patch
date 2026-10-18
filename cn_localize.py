#!/usr/bin/env python3
"""LM Studio 中文补丁交互入口：apply / restore / status。"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
JS = os.path.join(HERE, "resources", "app", ".webpack", "renderer", "main_window.js")
BACKUP = os.path.join(HERE, ".backups", "main_window.js.original")
BACKUP_VERSION = BACKUP + ".version"
APP_PACKAGE = os.path.join(HERE, "resources", "app", "package.json")
EXE = os.path.join(HERE, "LM Studio.exe")


def rule():
    print("=" * 52)


def ask(prompt, default="y"):
    hint = "[Y/n]" if default == "y" else "[y/N]"
    try:
        ans = input(f"{prompt} {hint} ").strip().lower()
    except EOFError:
        return False
    if not ans:
        ans = default
    return ans in ("y", "yes", "是")


def is_chinese():
    if not os.path.exists(JS):
        return None
    with open(JS, "rb") as f:
        data = f.read()
    return b'lng:"zh_CN"' in data


def lms_pids():
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq LM Studio.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
        ).stdout
    except OSError:
        return []
    text = out.decode("mbcs", "ignore")
    pids = []
    for line in text.splitlines():
        if line.startswith('"LM Studio.exe"'):
            parts = line.split('","')
            if len(parts) > 1:
                pids.append(parts[1])
    return pids


def ensure_closed():
    pids = lms_pids()
    if not pids:
        print("LM Studio 未运行，可以直接修改界面文件。")
        return True
    print(f"检测到 LM Studio 正在运行（PID: {', '.join(pids)}）。")
    print("补丁需要写入界面文件，必须先关闭 LM Studio。")
    if not ask("是否现在关闭 LM Studio 并继续？"):
        print("已取消，未做任何修改。")
        return False
    subprocess.run(["taskkill", "/IM", "LM Studio.exe"], capture_output=True)
    for _ in range(10):
        time.sleep(1)
        if not lms_pids():
            print("LM Studio 已关闭。")
            return True
    left = lms_pids()
    print(f"仍有后台进程未退出（PID: {', '.join(left)}）。")
    if ask("是否强制关闭？未保存的对话可能丢失。", "n"):
        subprocess.run(["taskkill", "/F", "/IM", "LM Studio.exe"], capture_output=True)
        time.sleep(2)
        if not lms_pids():
            print("LM Studio 已强制关闭。")
            return True
    print("已中止：请手动完全退出 LM Studio（含托盘图标）后重试。")
    return False


def run_script(script, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, script), "--path", HERE, *args],
        capture_output=True,
        env=env,
    )
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


def pick(pattern, text):
    m = re.search(pattern, text)
    return int(m.group(1)) if m else 0


def syntax_ok():
    try:
        r = subprocess.run(["node", "--check", JS], capture_output=True)
    except FileNotFoundError:
        return None
    return r.returncode == 0


def maybe_restart():
    if not ask("现在重新启动 LM Studio？"):
        print("请稍后手动打开 LM Studio。")
        return
    if not os.path.exists(EXE):
        print("未找到 LM Studio.exe，请手动启动。")
        return
    subprocess.Popen([EXE], cwd=HERE, creationflags=subprocess.DETACHED_PROCESS)
    print("已启动 LM Studio，请稍候等界面加载完成。")


def app_version():
    try:
        with open(APP_PACKAGE, "r", encoding="utf-8") as f:
            return str(json.load(f).get("version") or "")
    except (OSError, ValueError):
        return ""


def backup_version():
    try:
        with open(BACKUP_VERSION, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def write_backup_version(ver):
    try:
        with open(BACKUP_VERSION, "w", encoding="utf-8") as f:
            f.write(ver)
    except OSError:
        pass


def backup_state():
    """返回 (是否存在, 备份记录的版本, 是否与当前版本不符)。"""
    if not os.path.exists(BACKUP):
        return False, "", False
    cur = app_version()
    bver = backup_version()
    if not cur:
        return True, bver, False
    if bver:
        return True, bver, bver != cur
    try:
        stale = os.path.getmtime(BACKUP) < os.path.getmtime(APP_PACKAGE)
    except OSError:
        stale = False
    return True, bver, stale


def rotate_stale_backup(current):
    exists, bver, stale = backup_state()
    if not exists or not current:
        return False
    if not stale:
        if bver != current:
            write_backup_version(current)
        return False
    old = bver or "unknown"
    safe = re.sub(r"[^0-9A-Za-z._+-]", "_", old) or "unknown"
    target = f"{BACKUP}.{safe}"
    n = 2
    while os.path.exists(target):
        target = f"{BACKUP}.{safe}.{n}"
        n += 1
    os.rename(BACKUP, target)
    try:
        os.remove(BACKUP_VERSION)
    except OSError:
        pass
    print(f"检测到 LM Studio 版本变化（备份 {old} → 当前 {current}）。")
    print(f"旧备份已存档为：{os.path.basename(target)}")
    print("将按当前版本重新备份英文界面文件。")
    return True


def do_status():
    rule()
    print("  LM Studio 中文补丁 - 状态")
    rule()
    state = is_chinese()
    if state is None:
        print("界面文件：未找到，路径可能不正确")
        return 1
    print("界面语言：" + ("中文（已汉化）" if state else "英文（未汉化）"))
    cur = app_version()
    print("当前版本：" + (cur or "未知"))
    exists, bver, stale = backup_state()
    if not exists:
        print("原始备份：不存在")
    else:
        print("原始备份：存在（" + (bver or "未记录版本") + "）")
        if stale:
            print("警告：备份版本与当前版本不符，无法用于还原。")
            print("      重新应用中文补丁时会自动存档旧备份并重建。")
    print("运行状态：" + ("LM Studio 正在运行" if lms_pids() else "LM Studio 未运行"))
    return 0


def do_apply():
    rule()
    print("  LM Studio 简体中文补丁 - 应用中文")
    rule()
    state = is_chinese()
    if state is None:
        print("错误：找不到 LM Studio 界面文件，安装目录可能不正确。")
        return 1
    if state:
        print("当前已经是中文界面。将重新执行补丁，补齐遗漏的文案。")
    else:
        print("当前为英文界面。将安装上游补丁和增强补丁。")
    print()
    if not ensure_closed():
        return 0
    current = app_version()
    rotate_stale_backup(current)

    print()
    print("正在执行上游汉化补丁……")
    rc1, out1 = run_script("patch_lmstudio.py")
    if rc1 != 0:
        print("上游补丁失败，输出如下：")
        print(out1.strip())
        return 1
    up = pick(r"共替换\s*(\d+)\s*处", out1)
    if current and os.path.exists(BACKUP):
        write_backup_version(current)

    print("正在执行增强补丁……")
    rc2, out2 = run_script("patch_extra.py")
    if rc2 != 0:
        print("增强补丁失败，输出如下：")
        print(out2.strip())
        print("界面可能处于半汉化状态，可运行 1-还原英文.cmd 还原。")
        return 1
    attr = pick(r"属性替换\s*(\d+)\s*处", out2)
    plain = pick(r"纯文本替换\s*(\d+)\s*处", out2)

    check = syntax_ok()
    if check is False:
        print("错误：补丁后的界面文件语法检查未通过，正在自动还原……")
        rc3, out3 = run_script("patch_lmstudio.py", "--restore")
        print("已还原为英文界面。" if rc3 == 0 else "自动还原失败，请运行 1-还原英文.cmd。")
        return 1

    print()
    rule()
    print("  完成")
    rule()
    print(f"上游补丁：替换 {up} 处")
    print(f"增强补丁：属性 {attr} 处，纯文本 {plain} 处")
    if up + attr + plain == 0:
        print("没有新的可替换文案，界面已是中文。")
    print("原始备份：" + (BACKUP if os.path.exists(BACKUP) else "无"))
    print()
    print("提示：LM Studio 更新后会覆盖界面文件，界面会变回英文。")
    print("      届时重新双击 0-应用中文.cmd 即可。")
    print()
    maybe_restart()
    return 0


def do_restore():
    rule()
    print("  LM Studio 中文补丁 - 还原英文")
    rule()
    exists, bver, stale = backup_state()
    if not exists:
        print("错误：找不到原始备份，无法还原。")
        print(f"备份路径：{BACKUP}")
        return 1
    if stale:
        cur = app_version()
        print("错误：备份来自旧版本，不能还原到当前版本。")
        print(f"  备份版本：{bver or '未记录（文件时间早于当前版本）'}")
        print(f"  当前版本：{cur or '未知'}")
        print("强行还原会把旧版界面文件写到新版程序里，可能导致界面无法启动。")
        print("请重新双击 0-应用中文.cmd，它会自动存档旧备份并按当前版本重建。")
        return 1
    print("将把界面文件恢复为安装补丁前的英文原版。")
    print("注意：这不是卸载 LM Studio，只还原界面文本。")
    print()
    if not ensure_closed():
        return 0
    print()
    print("正在还原……")
    rc, out = run_script("patch_lmstudio.py", "--restore")
    if rc != 0:
        print("还原失败，输出如下：")
        print(out.strip())
        return 1
    print()
    rule()
    print("  完成：界面已恢复英文")
    rule()
    print("原始备份仍然保留，可随时重新双击 0-应用中文.cmd。")
    print()
    maybe_restart()
    return 0


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    if action == "status":
        return do_status()
    if action == "apply":
        rc = do_apply()
    elif action == "restore":
        rc = do_restore()
    else:
        print("用法：cn_localize.py [apply|restore|status]")
        return 2
    print()
    try:
        input("按回车键退出……")
    except EOFError:
        pass
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
