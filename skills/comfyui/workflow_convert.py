#!/usr/bin/env python3
"""
ComfyUI UI 格式工作流 JSON → API 格式转换器。

UI 格式: {"nodes": [...], "links": [...]}（ComfyUI 前端导出的 .json）
API 格式: {"<node_id>": {"class_type": ..., "inputs": {...}}}（POST /prompt 用的）

输入名解析:
  1. 优先用 ComfyUI(aki 魔改前端)导出自带的 widgets_values_named；
  2. 否则按 widgets_values 顺序 + object_info 的输入定义映射（可选传入）。
只保留 mode==0 的节点（bypass/muted 丢弃）。纯 stdlib，无依赖。
"""

# 前端小部件键，不是后端输入，需要剥离
_FRONTEND_ONLY_KEYS = {
    "control_after_generate",
    "Node name for S&R",
    "aux_id",
    "cnr_id",
    "ver",
}


def ui_to_api(ui_graph, object_info=None):
    """ui_graph: 解析后的 UI 格式 dict。object_info: 可选，ComfyUI /object_info 响应。

    返回 (api_graph, warnings)。
    """
    if "nodes" not in ui_graph:
        raise ValueError("not a UI-format workflow (missing 'nodes' array)")

    nodes = ui_graph.get("nodes") or []
    links = {l[0]: l for l in (ui_graph.get("links") or [])}
    warnings = []
    api = {}

    for n in nodes:
        mode = n.get("mode", 0)
        if mode in (2, 4):  # muted / bypassed
            continue
        nid = str(n["id"])
        ctype = n.get("type")
        if not ctype:
            continue
        inputs = {}

        # 1) 连线输入: name -> [origin_node_id, origin_slot]
        for inp in n.get("inputs", []) or []:
            lid = inp.get("link")
            if lid is None or not isinstance(inp.get("name"), str):
                continue
            l = links.get(lid)
            if not l:
                warnings.append(f"node {nid} input {inp['name']}: link {lid} missing")
                continue
            inputs[inp["name"]] = [str(l[1]), l[2]]

        # 2) 小部件输入
        named = n.get("widgets_values_named")
        if isinstance(named, dict) and named:
            for k, v in named.items():
                if k in _FRONTEND_ONLY_KEYS or k in inputs:
                    continue
                inputs[k] = v
        else:
            vals = n.get("widgets_values")
            if isinstance(vals, list) and vals:
                if not object_info or ctype not in object_info:
                    warnings.append(
                        f"node {nid} ({ctype}): widgets_values 无命名映射，"
                        f"需 ComfyUI 在线时经 object_info 转换")
                else:
                    for k, v in _map_positional(ctype, vals, object_info, inputs, nid, warnings):
                        inputs[k] = v

        api[nid] = {"class_type": ctype, "inputs": inputs}

    if not api:
        raise ValueError("workflow has no active nodes")
    api = _prune_unreferenced(api, warnings)
    if not api:
        raise ValueError("workflow has no nodes reachable from output nodes")
    return api, warnings


def _is_output_node(ctype):
    return ctype.startswith(("Save", "Preview", "Webcam", "Send")) or "Save" in ctype


def _prune_unreferenced(api, warnings):
    """Keep only nodes transitively feeding an output node (ComfyUI drops the
    rest at execution anyway; dropping them here avoids validation errors
    from orphaned half-wired samplers)."""
    referenced = set()
    for n in api.values():
        for v in n["inputs"].values():
            if isinstance(v, list) and len(v) == 2:
                referenced.add(str(v[0]))
    outputs = [nid for nid, n in api.items() if _is_output_node(n["class_type"])]
    if not outputs:
        return api  # no recognizable output: keep everything
    keep = set()
    stack = list(outputs)
    while stack:
        nid = stack.pop()
        if nid in keep:
            continue
        keep.add(nid)
        for v in api.get(nid, {}).get("inputs", {}).values():
            if isinstance(v, list) and len(v) == 2:
                stack.append(str(v[0]))
    dropped = [f"{nid}:{api[nid]['class_type']}"
               for nid in api if nid not in keep and nid not in referenced]
    if dropped:
        warnings.append("剪枝未接入输出的节点: " + ", ".join(dropped))
    return {nid: n for nid, n in api.items() if nid in keep}


def _map_positional(ctype, vals, object_info, inputs, nid, warnings):
    """按 object_info 输入定义顺序映射 widgets_values（best-effort）。"""
    spec = (object_info.get(ctype) or {}).get("input", {}) or {}
    ordered = []
    for section in ("required", "optional"):
        for name, sdef in (spec.get(section) or {}).items():
            if name in inputs:  # 已作为连线处理
                continue
            t = sdef[0] if isinstance(sdef, list) and sdef else sdef
            if isinstance(t, list):
                continue  # 连线类型 (["MODEL"] 等)
            ordered.append(name)
    for i, name in enumerate(ordered):
        if i >= len(vals):
            break
        yield name, vals[i]
    if len(vals) > len(ordered):
        warnings.append(f"node {nid} ({ctype}): {len(vals)-len(ordered)} 个 widget 值未能映射")


def find_prompt_nodes(api_graph):
    """返回 (sampler_ids, positive_encode_ids, negative_encode_ids)。"""
    samplers = [nid for nid, n in api_graph.items()
                if n["class_type"] in ("KSampler", "KSamplerAdvanced")]
    pos, neg = set(), set()
    for nid in samplers:
        for role, sink in (("positive", pos), ("negative", neg)):
            ref = api_graph[nid]["inputs"].get(role)
            if isinstance(ref, list) and len(ref) == 2:
                sink.add(str(ref[0]))
    return samplers, pos, neg
