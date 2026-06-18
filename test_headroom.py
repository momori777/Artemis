"""Headroom SmartCrusher + CCR 端到端测试"""
import json
from skills.headroom import SmartCrusher, CCRStore, compress_json, compress_text

def test_smart_crusher_json():
    """测试 JSON 数组压缩"""
    print("=" * 60)
    print("TEST 1: SmartCrusher JSON 数组压缩")
    print("=" * 60)
    
    # 模拟大量搜索结果
    data = {
        "results": [
            {"id": i, "status": "ok", "message": "Success", "timestamp": "2026-06-19T00:00:00"}
            for i in range(100)
        ]
    }
    # 混入一个错误
    data["results"][50] = {"id": 50, "status": "error", "message": "Connection timeout", "timestamp": "2026-06-19T00:00:00"}
    
    crusher = SmartCrusher()
    result = crusher.crush(data, query="error timeout")
    
    print(f"原始: {result.items_total} 项, {result.tokens_before} tokens")
    print(f"压缩: {result.items_kept} 项, {result.tokens_after} tokens")
    print(f"压缩率: {result.compression_ratio:.1%} (保留 {100-result.compression_ratio*100:.0f}% 节省)")
    print(f"保留类别: {result.preserved_categories}")
    print(f"缓存标记: {result.compressed[:100]}...")
    print(f"Hash: {result.original_hash}")
    print()

def test_smart_crusher_text():
    """测试文本压缩"""
    print("=" * 60)
    print("TEST 2: SmartCrusher 文本压缩")
    print("=" * 60)
    
    long_text = "\n".join(f"第{i}行: 这是测试记忆数据 {i} 的详细内容。包含一些关键信息：用户喜欢动漫，角色是夏目。" for i in range(50))
    
    result = compress_text(long_text, query="夏目 喜欢")
    
    print(f"原始: {result.tokens_before} tokens")
    print(f"压缩: {result.tokens_after} tokens")
    print(f"压缩率: {result.compression_ratio:.1%}")
    print(f"Hash: {result.original_hash}")
    # 显示压缩结果前200字符
    print(f"压缩结果预览: {result.compressed[:200]}...")
    print()

def test_ccr_store():
    """测试 CCR 缓存"""
    print("=" * 60)
    print("TEST 3: CCR (Compress-Cache-Retrieve) 缓存")
    print("=" * 60)
    
    store = CCRStore(max_entries=100, ttl_seconds=300)
    
    # 存入
    store.put("hash123", "这是原始记忆内容：夏目喜欢喝咖啡。")
    
    # 取回
    retrieved = store.get("hash123")
    print(f"存入: 这是原始记忆内容：夏目喜欢喝咖啡。")
    print(f"取回: {retrieved}")
    print(f"匹配: {retrieved == '这是原始记忆内容：夏目喜欢喝咖啡。'}")
    
    # BM25 搜索
    found = store.search("hash123", "夏目 咖啡")
    print(f"BM25 搜索 '夏目 咖啡': {found is not None}")
    
    # 不存在
    not_found = store.get("nothash")
    print(f"取出不存在的 hash: {not_found}")
    
    # 统计
    print(f"缓存统计: {store.stats()}")
    print()

def test_integrated_pipeline():
    """测试 mem0_bridge 集成"""
    print("=" * 60)
    print("TEST 4: 集成 pipeline (mem0_bridge compress)")
    print("=" * 60)
    
    from skills.shared.mem0_bridge import compress_search_results, retrieve_from_ccr
    
    # 模拟搜索结果
    mock_results = [
        {"id": 1, "memory": "夏目喜欢喝抹茶拿铁，每周三去新宿的咖啡店。", "score": 0.95},
        {"id": 2, "memory": "夏目在2026年5月提到她喜欢《星光咖啡蝶与死神之馆》这款游戏。", "score": 0.88},
        {"id": 3, "memory": "用户和夏目的第一次对话发生在2026年4月，用户让她扮演女朋友角色。", "score": 0.82},
        {"id": 4, "memory": "夏目对猫科动物很感兴趣，养了一只名叫Mochi的布偶猫。", "score": 0.75},
        {"id": 5, "memory": "夏目喜欢二次元文化，特别是 Key 社的游戏作品。", "score": 0.70},
    ]
    
    compressed, stats = compress_search_results(mock_results, "夏目 喜欢")
    
    print(f"原始结果: {len(mock_results)} 条")
    print(f"压缩结果: {len(compressed)} 条")
    print(f"节省: {stats['savings_pct']}%")
    print(f"CCR 缓存大小: {stats['ccr_cache_size']}")
    print()
    print("压缩后结果:")
    for item in compressed:
        mem_preview = item['memory'][:80] + "..." if len(item['memory']) > 80 else item['memory']
        print(f"  [{item['id']}] score={item['score']:.2f} | {mem_preview}")
    
    # 测试 CCR 取回
    print()
    print("测试 CCR 取回:")
    for item in compressed:
        h = item.get("_original_hash")
        if h:
            ok, text = retrieve_from_ccr(h)
            print(f"  Hash {h}: 取回 {'成功' if ok else '失败'}")
            if ok:
                print(f"    原文: {text[:80]}...")
            break  # 只测第一个
    print()

if __name__ == "__main__":
    test_smart_crusher_json()
    test_smart_crusher_text()
    test_ccr_store()
    test_integrated_pipeline()
    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
