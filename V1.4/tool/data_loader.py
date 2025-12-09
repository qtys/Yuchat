import os
import json
import glob

_default_data = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Sed blandit libero volutpat sed cras ornare arcu. Nisl vel pretium "
    "lectus quam id leo in. Tincidunt arcu non sodales neque sodales ut etiam.",
    "Elit scelerisque mauris pellentesque pulvinar pellentesque habitant. "
    "Nisl rhoncus mattis rhoncus urna neque. Orci nulla pellentesque "
    "dignissim enim. Ac auctor augue mauris augue neque gravida in fermentum. "
    "Lacus suspendisse faucibus interdum posuere."
]

def _parse_obj(obj, items):
    if isinstance(obj, list):
        for e in obj:
            if isinstance(e, str):
                items.append(e)
            elif isinstance(e, dict):
                txt = e.get("text") or e.get("message") or e.get("content")
                if isinstance(txt, str):
                    items.append(txt)
    elif isinstance(obj, dict):
        if "messages" in obj and isinstance(obj["messages"], list):
            for e in obj["messages"]:
                if isinstance(e, str):
                    items.append(e)
                elif isinstance(e, dict):
                    txt = e.get("text") or e.get("message") or e.get("content")
                    if isinstance(txt, str):
                        items.append(txt)
        else:
            txt = obj.get("text") or obj.get("message") or obj.get("content")
            if isinstance(txt, str):
                items.append(txt)
    elif isinstance(obj, str):
        items.append(obj)

def load_data_from_folder(folder_name="data"):
    """返回 list：从 project/data/*.json 读取的完整 JSON 对象，若没有则返回内置默认数据。"""
    items = []
    base_fs = os.path.join(os.path.dirname(__file__), "..", folder_name)
    base_fs = os.path.normpath(base_fs)
    if os.path.isdir(base_fs):
        for path in sorted(glob.glob(os.path.join(base_fs, "*.json"))):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                    # 如果加载的是列表，直接添加到结果中
                    if isinstance(obj, list):
                        items.extend(obj)
                    else:
                        items.append(obj)
            except Exception:
                continue

    # 若没读到，尝试包内资源（可选，视打包方式）
    if not items:
        try:
            import importlib.resources as pkg_resources
        except Exception:
            pkg_resources = None

        if pkg_resources:
            pkg = __package__ or ""
            resource_pkg = pkg if pkg else None
            try:
                try:
                    files = pkg_resources.files(resource_pkg / folder_name) if resource_pkg else pkg_resources.files(folder_name)
                    for entry in files.iterdir():
                        if entry.name.endswith(".json"):
                            try:
                                with pkg_resources.as_file(entry) as p:
                                    with open(p, "r", encoding="utf-8") as f:
                                        obj = json.load(f)
                                        if isinstance(obj, list):
                                            items.extend(obj)
                                        else:
                                            items.append(obj)
                            except Exception:
                                continue
                except Exception:
                    base_resource = (resource_pkg + "." + folder_name) if resource_pkg else folder_name
                    for name in pkg_resources.contents(base_resource):
                        if name.endswith(".json"):
                            try:
                                with pkg_resources.open_text(base_resource, name, encoding="utf-8") as f:
                                    obj = json.load(f)
                                    if isinstance(obj, list):
                                        items.extend(obj)
                                    else:
                                        items.append(obj)
                            except Exception:
                                continue
            except Exception:
                pass

    # 如果还是没有数据，返回默认的文本数据
    if not items:
        return _default_data
    
    return items