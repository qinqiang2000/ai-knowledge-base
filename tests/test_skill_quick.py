"""
快速测试 customer-service skill

简化版测试脚本，快速验证 skill 基本功能
"""
import asyncio
from api.models.requests import QueryRequest
from api.services.agent_service import AgentService
from api.services.session_service import InMemorySessionService


async def quick_test(query: str):
    """快速测试单个查询"""
    print(f"\n{'='*70}")
    print(f"查询: {query}")
    print(f"{'='*70}\n")

    session_service = InMemorySessionService()
    agent_service = AgentService(session_service)

    request = QueryRequest(
        tenant_id="test-tenant",
        prompt=query,
        skill="customer-service",
        language="zh-CN"
    )

    try:
        async for event in agent_service.process_query(request):
            if event.get("type") == "assistant_message":
                content = event.get("content", "")
                if content:
                    print(content, end="", flush=True)

            elif event.get("type") == "tool_use":
                tool_name = event.get("tool_name")
                tool_input = event.get("tool_input", {})

                # 简化显示工具调用
                if tool_name == "Grep":
                    pattern = tool_input.get("pattern", "")
                    path = tool_input.get("path", "")
                    print(f"\n[🔍 搜索: {pattern} in {path}]", flush=True)
                elif tool_name == "Read":
                    file_path = tool_input.get("file_path", "")
                    print(f"\n[📖 读取: {file_path}]", flush=True)

        print("\n")

    except Exception as e:
        print(f"\n❌ 错误: {e}\n")
        import traceback
        traceback.print_exc()


async def main():
    """运行预定义的快速测试"""
    print("""
╭────────────────────────────────────────────╮
│ 发票云客服 Skill 快速测试                 │
╰────────────────────────────────────────────╯
    """)

    # 定义要测试的查询
    test_queries = [
        "标准版开票如何配置数电票？",           # 完整问题，应该直接搜索
        "如何开票？",                            # 不完整问题，应该询问产品
        "星瀚旗舰版收票勾选流程是什么？",       # 产品区分测试
        "乐企通道如何配置？",                    # 辅助系统测试
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n【测试 {i}/{len(test_queries)}】")
        await quick_test(query)

        if i < len(test_queries):
            print("\n" + "-"*70)
            await asyncio.sleep(1)  # 短暂延迟，避免请求过快

    print("\n✅ 所有快速测试完成！\n")


if __name__ == "__main__":
    # 可以通过命令行参数自定义测试
    import sys

    if len(sys.argv) > 1:
        # 自定义查询
        custom_query = " ".join(sys.argv[1:])
        asyncio.run(quick_test(custom_query))
    else:
        # 运行预定义测试
        asyncio.run(main())
