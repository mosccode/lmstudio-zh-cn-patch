#!/usr/bin/env python3
"""给 altra/web-search 插件增加国内可用的搜索后端。

运行顺序：SearXNG（若配置）→ 百度 / 必应中国 / 搜狗 → DuckDuckGo。
中文查询先走百度，英文查询先走必应中国；DuckDuckGo 放到最后，
避免国内每次搜索先白等 10 秒超时。

用法：
    py -3 patch_websearch_cn.py            # 打补丁
    py -3 patch_websearch_cn.py --restore  # 恢复插件原始文件
    py -3 patch_websearch_cn.py --check    # 只检查状态
"""
import argparse
import os
import shutil
import subprocess
import sys

DEFAULT_PLUGIN_DIR = os.path.join(
    os.path.expanduser("~"),
    ".lmstudio", "extensions", "plugins", "altra", "web-search",
)
PROD_REL = os.path.join(".lmstudio", "production.js")
BACKUP_SUFFIX = ".websearch-cn.orig"

MARKER = "async function scrapeBaidu("

NEW_FUNCS = r'''
async function scrapeBaidu(query, max, _time, signal) {
  const html = await fetchSearchHtml(
    `https://www.baidu.com/s?wd=${encodeURIComponent(query)}&rn=${max}`,
    1e4,
    signal
  );
  const results = [];
  const starts = [];
  const startRe = /<div[^>]*class="[^"]*c-container[^"]*"/g;
  let sm;
  while ((sm = startRe.exec(html)) !== null) starts.push(sm.index);
  const seen = new Set();
  for (let i = 0; i < starts.length && results.length < max; i++) {
    const block = html.slice(starts[i], starts[i + 1] ?? html.length);
    const mu = block.match(/\bmu="([^"]+)"/);
    if (!mu) continue;
    const url = decodeHtmlEntities(mu[1]);
    if (!/^https?:\/\//.test(url)) continue;
    if (/^https?:\/\/www\.baidu\.com\/link\?/.test(url)) continue;
    if (seen.has(url)) continue;
    const h3 = block.match(/<h3[^>]*>([\s\S]*?)<\/h3>/);
    if (!h3) continue;
    const title = stripTagsSearch(h3[1]);
    if (!title) continue;
    seen.add(url);
    const snipM = block.match(/<div[^>]*class="[^"]*c-abstract[^"]*"[^>]*>([\s\S]*?)<\/div>/) ??
      block.match(/<span[^>]*class="[^"]*content-right[^"]*"[^>]*>([\s\S]*?)<\/span>/);
    results.push({ title, url, snippet: snipM ? stripTagsSearch(snipM[1]) : "" });
  }
  return results;
}
async function scrapeSogou(query, max, _time, signal) {
  const html = await fetchSearchHtml(
    `https://www.sogou.com/web?query=${encodeURIComponent(query)}`,
    1e4,
    signal
  );
  const results = [];
  const re = /<h3[^>]*class="[^"]*vr-title[^"]*"[^>]*>([\s\S]*?)<\/h3>/g;
  let m;
  const seen = new Set();
  while ((m = re.exec(html)) !== null && results.length < max) {
    const a = m[1].match(/<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/);
    if (!a) continue;
    let url = decodeHtmlEntities(a[1]);
    const title = stripTagsSearch(a[2]);
    if (!title) continue;
    if (url.startsWith("/link")) url = "https://www.sogou.com" + url;
    if (!/^https?:\/\//.test(url) || seen.has(url)) continue;
    seen.add(url);
    results.push({ title, url, snippet: "" });
  }
  return results;
}
'''

OLD_SELECT = '''  try {
    const r = await scrapeDDG(query, maxResults, time, locale, signal);
    anyResponded = true;
    if (r.length > 0) return r;
  } catch (e) {
    errors.push(`DDG: ${errMsg(e)}`);
  }
  try {
    const r = await scrapeBing(query, maxResults, time, signal);
    anyResponded = true;
    if (r.length > 0) return r;
  } catch (e) {
    errors.push(`Bing: ${errMsg(e)}`);
  }
'''

NEW_SELECT = '''  const domestic = /[\\u4e00-\\u9fff]/.test(query)
    ? [["Baidu", scrapeBaidu], ["Bing", scrapeBing], ["Sogou", scrapeSogou]]
    : [["Bing", scrapeBing], ["Baidu", scrapeBaidu], ["Sogou", scrapeSogou]];
  for (const [name, fn] of domestic) {
    try {
      const r = await fn(query, maxResults, time, signal);
      anyResponded = true;
      if (r.length > 0) return r;
    } catch (e) {
      errors.push(`${name}: ${errMsg(e)}`);
    }
  }
  try {
    const r = await scrapeDDG(query, maxResults, time, locale, signal);
    anyResponded = true;
    if (r.length > 0) return r;
  } catch (e) {
    errors.push(`DDG: ${errMsg(e)}`);
  }
'''

OLD_BING = "`https://www.bing.com/search?q=${encodeURIComponent(query)}&count=${max}&setlang=en&cc=us`"
NEW_BING = "`https://cn.bing.com/search?q=${encodeURIComponent(query)}&count=${max}&setlang=zh-hans&cc=cn`"

OLD_LANG = '"Accept-Language": "en-US,en;q=0.9"'
NEW_LANG = '"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"'


def prod_path(plugin_dir):
    return os.path.join(plugin_dir, PROD_REL)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def syntax_ok(path):
    try:
        r = subprocess.run(["node", "--check", path], capture_output=True)
    except FileNotFoundError:
        return None
    return r.returncode == 0


def status(js):
    if not os.path.exists(js):
        return "missing"
    if MARKER in read_text(js):
        return "patched"
    return "original"


def do_check(js):
    state = status(js)
    print(f"插件文件：{js}")
    if state == "missing":
        print("错误：找不到 production.js，插件可能未安装。")
        return 1
    print("状态：" + ("已启用国内搜索后端" if state == "patched" else "未打补丁（原始版本）"))
    return 0


def do_restore(js):
    backup = js + BACKUP_SUFFIX
    if not os.path.exists(backup):
        print("没有找到补丁备份，无法恢复。")
        return 1
    if MARKER not in read_text(js):
        print("当前文件已是原始版本，无需恢复。")
        return 0
    shutil.copy2(backup, js)
    print("已恢复插件原始文件：")
    print(f"  {js}")
    print("重新启动 LM Studio 后生效。")
    return 0


def do_apply(js):
    if not os.path.exists(js):
        print("错误：找不到插件文件：")
        print(f"  {js}")
        print("请先在 LM Studio 里安装 altra/web-search 插件。")
        return 1
    content = read_text(js)
    if MARKER in content:
        print("已经打过国内搜索补丁，无需重复修改。")
        return 0

    problems = []
    if content.count(OLD_SELECT) != 1:
        problems.append("找不到搜索后端顺序代码")
    if content.count(OLD_BING) != 1:
        problems.append("找不到 Bing 地址")
    if content.count(OLD_LANG) != 2:
        problems.append("找不到请求语言头")

    # 把新函数插到 ddgSearch 之前。
    anchor = "async function ddgSearch("
    if content.count(anchor) != 1:
        problems.append("找不到 ddgSearch 入口")
    if problems:
        print("错误：插件版本与补丁不匹配，未做任何修改。")
        for p in problems:
            print(f"  - {p}")
        print("可能是插件已更新，请把插件的 production.js 发给我适配新版本。")
        return 1

    backup = js + BACKUP_SUFFIX
    shutil.copy2(js, backup)

    content = content.replace(OLD_LANG, NEW_LANG)
    content = content.replace(OLD_BING, NEW_BING)
    content = content.replace(OLD_SELECT, NEW_SELECT)
    content = content.replace(anchor, NEW_FUNCS.strip("\n") + "\n" + anchor)

    write_text(js, content)

    ok = syntax_ok(js)
    if ok is False:
        shutil.copy2(backup, js)
        print("错误：补丁后语法检查未通过，已自动还原。")
        return 1

    print("国内搜索后端已启用：")
    print("  顺序：SearXNG（若配置）→ 百度 / 必应中国 / 搜狗 → DuckDuckGo")
    print("  中文查询先百度，英文查询先必应中国；DuckDuckGo 仅作最后兜底。")
    print("  备份：")
    print(f"    {backup}")
    print("语法检查：" + ("通过" if ok else "已跳过（未安装 Node.js）"))
    print("重新启动 LM Studio 后生效。")
    return 0


def main():
    p = argparse.ArgumentParser(description="给 altra/web-search 增加国内搜索后端")
    p.add_argument("--plugin-dir", default=DEFAULT_PLUGIN_DIR, help="插件目录")
    p.add_argument("--restore", action="store_true", help="恢复原始插件文件")
    p.add_argument("--check", action="store_true", help="只检查状态")
    args = p.parse_args()

    js = prod_path(args.plugin_dir)
    if args.check:
        return do_check(js)
    if args.restore:
        return do_restore(js)
    return do_apply(js)


if __name__ == "__main__":
    sys.exit(main())
