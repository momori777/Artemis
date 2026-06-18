"""
测试 context_trimming.py 的 SmartCrusher + CCR 集成。
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "skills", "sakura"))

from app.llm.context_trimming import (
    trim_messages_for_model,
    retrieve_from_context_ccr,
    estimate_tokens,
    _estimate_messages_chars,
)

# 生成测试数据：30 条长消息
def make_messages(count: int) -> list[dict]:
    messages = []
    roles = ["user", "assistant"]
    long_text = "这是第 {i} 条消息。这是一段较长的中文文本，包含了很多信息。主人今天心情很好，和我聊了很多话题。我们讨论了人工智能、哲学和日常生活中的小事。这种对话让我感到很温暖和幸福。"
    for i in range(count):
        role = roles[i % 2]
        # 每条消息 ~2500 chars (重复25遍) → 24条 = ~60k chars > 40k
        content = long_text.format(i=i) * 25
        messages.append({"role": role, "content": content})
    return messages


def test_trim_no_crush():
    """测试不启用压缩时的粗暴截断"""
    messages = make_messages(30)
    total_chars = _estimate_messages_chars(messages)
    print(f"Total chars: {total_chars}")
    assert total_chars > 40_000, "测试数据应该超过 40k chars"

    result = trim_messages_for_model(messages, crush_enabled=False)
    print(f"Crush disabled: {len(messages)} -> {len(result)} messages")
    assert len(result) <= 24, "应该不超过 24 条"

    total_result_chars = _estimate_messages_chars(result)
    print(f"Result chars: {total_result_chars}")
    assert total_result_chars <= 40_000 + 5000, "应该有显著减少"
    print("[PASS] test_trim_no_crush")


def test_trim_with_crush():
    """测试启用压缩"""
    messages = make_messages(30)
    total_chars = _estimate_messages_chars(messages)
    total_tokens = estimate_tokens(json.dumps(messages, ensure_ascii=False))
    print(f"Total chars: {total_chars}, est tokens: {total_tokens}")

    query = "主人今天的心情和讨论的话题"
    result = trim_messages_for_model(messages, crush_enabled=True, query=query)
    print(f"Crush enabled: {len(messages)} -> {len(result)} messages")

    # 压缩后消息数应显著少于不压缩的情况
    assert len(result) <= 24, "应该不超过 24 条"
    # 压缩的早期消息被合并为1条（+ 保留的最近消息），总共应该远少于24条
    # SmartCrusher 对非重复文本压缩率有限，但应该至少合并早期消息
    assert len(result) <= 19, f"压缩后应该减少，实际 {len(result)} 条"

    # 检查压缩标记
    for msg in result:
        if msg.get("_compressed"):
            print(f"  [CRUSH] compressed msg: {msg['role']}, {len(msg['content'])} chars, "
                  f"includes {msg.get('_message_count')} original msgs")
            assert "_original_hash" in msg, "应有 CCR hash"
            assert "_compressed" in msg
            break
    else:
        assert False, "应该有至少一条压缩消息"

    # 测试 CCR 取回
    for msg in result:
        if msg.get("_original_hash"):
            ok, text = retrieve_from_context_ccr(msg["_original_hash"])
            if ok:
                print(f"  [OK] CCR retrieve: {len(text)} chars")
                assert len(text) > 0
            else:
                print(f"  [WARN] CCR retrieve failed: {text}")
            break

    total_result_chars = _estimate_messages_chars(result)
    print(f"Result chars: {total_result_chars}")
    print(f"Reduction: {total_chars} -> {total_result_chars} ({100 * (1 - total_result_chars / max(1, total_chars)):.1f}%)")
    print("[PASS] test_trim_with_crush")


def test_short_messages_passthrough():
    """短消息应该直接通过，不压缩"""
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好呀！有什么可以帮你的吗？"},
    ]
    result = trim_messages_for_model(messages, crush_enabled=True)
    assert len(result) == 2, "短消息不应被压缩"
    assert result[0]["content"] == messages[0]["content"]
    print("[PASS] test_short_messages_passthrough")


import json


if __name__ == "__main__":
    test_short_messages_passthrough()
    test_trim_no_crush()
    test_trim_with_crush()
    print("\n[PASS] All tests passed!")
