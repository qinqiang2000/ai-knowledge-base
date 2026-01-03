"""
发票云客服 Skill 测试用例

测试 customer-service skill 在各种场景下的表现
"""
import asyncio
import sys

from api.models.requests import QueryRequest
from api.services.agent_service import AgentService
from api.services.session_service import InMemorySessionService


class SkillTester:
    """Skill 测试器"""

    def __init__(self):
        self.session_service = InMemorySessionService()
        self.agent_service = AgentService(self.session_service)
        self.test_results = []

    async def run_test(
        self,
        test_name: str,
        query: str,
        expected_behaviors: list[str],
        tenant_id: str = "test-tenant"
    ):
        """运行单个测试用例"""
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print(f"{'='*60}")
        print(f"输入: {query}")
        print(f"\n预期行为:")
        for behavior in expected_behaviors:
            print(f"  ✓ {behavior}")
        print(f"\n实际响应:")
        print("-" * 60)

        # 创建请求
        request = QueryRequest(
            tenant_id=tenant_id,
            prompt=query,
            skill="customer-service",
            language="zh-CN"
        )

        # 收集响应
        full_response = ""
        tool_uses = []

        try:
            async for event in self.agent_service.process_query(request):
                if event.get("type") == "assistant_message":
                    content = event.get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        full_response += content

                elif event.get("type") == "tool_use":
                    tool_name = event.get("tool_name")
                    tool_input = event.get("tool_input", {})
                    tool_uses.append({
                        "tool": tool_name,
                        "input": tool_input
                    })

            print("\n" + "-" * 60)

            # 记录工具使用
            if tool_uses:
                print(f"\n使用的工具:")
                for tool_use in tool_uses:
                    tool_name = tool_use["tool"]
                    tool_input = tool_use["input"]
                    print(f"  - {tool_name}")

                    # 显示关键参数
                    if tool_name == "Grep":
                        pattern = tool_input.get("pattern", "")
                        path = tool_input.get("path", "./data/kb")
                        print(f"    pattern: {pattern}")
                        print(f"    path: {path}")
                    elif tool_name == "Glob":
                        pattern = tool_input.get("pattern", "")
                        print(f"    pattern: {pattern}")
                    elif tool_name == "Read":
                        file_path = tool_input.get("file_path", "")
                        print(f"    file: {file_path}")

            # 记录结果
            self.test_results.append({
                "test_name": test_name,
                "query": query,
                "response": full_response,
                "tool_uses": tool_uses,
                "expected_behaviors": expected_behaviors
            })

            print(f"\n✅ 测试完成")

        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.test_results.append({
                "test_name": test_name,
                "query": query,
                "error": str(e),
                "expected_behaviors": expected_behaviors
            })

    def print_summary(self):
        """打印测试摘要"""
        print(f"\n\n{'='*60}")
        print(f"测试摘要")
        print(f"{'='*60}")
        print(f"总测试数: {len(self.test_results)}")

        passed = sum(1 for r in self.test_results if "error" not in r)
        failed = sum(1 for r in self.test_results if "error" in r)

        print(f"通过: {passed}")
        print(f"失败: {failed}")

        if failed > 0:
            print(f"\n失败的测试:")
            for result in self.test_results:
                if "error" in result:
                    print(f"  ❌ {result['test_name']}: {result['error']}")


async def main():
    """主测试函数"""
    tester = SkillTester()

    # 场景 1: 测试产品识别 - 完整问题
    await tester.run_test(
        test_name="场景1: 产品识别 - 标准版开票",
        query="标准版开票如何配置数电票？",
        expected_behaviors=[
            "识别产品线为：标准版",
            "识别功能模块为：开票",
            "搜索 kb/产品与交付知识/11-常见问题/标准版发票云问题/ 或 一问一答/标准版/开票.md",
            "不应混淆其他产品线（星瀚、星空）"
        ]
    )

    # 场景 2: 测试产品区分 - 星瀚旗舰版
    await tester.run_test(
        test_name="场景2: 产品区分 - 星瀚旗舰版收票",
        query="星瀚旗舰版收票勾选流程是什么？",
        expected_behaviors=[
            "识别产品线为：星瀚旗舰版",
            "识别功能模块为：收票",
            "搜索星瀚旗舰版相关文档",
            "不应使用标准版或星空旗舰版的答案"
        ]
    )

    # 场景 3: 测试问题完整性 - 缺少产品信息
    await tester.run_test(
        test_name="场景3: 问题完整性检查 - 缺少产品信息",
        query="如何开票？",
        expected_behaviors=[
            "识别问题不完整（缺少产品线）",
            "询问用户使用哪个产品（标准版、星瀚、星空等）",
            "不应直接搜索所有产品的答案",
            "等待用户明确产品后再继续"
        ]
    )

    # 场景 4: 测试 API 相关问题
    await tester.run_test(
        test_name="场景4: API 相关问题",
        query="开票接口的 API 文档在哪里？如何调用？",
        expected_behaviors=[
            "识别为 API 相关问题（关键词：API、接口）",
            "优先搜索 kb/API文档/",
            "如果 API文档/ 为空，搜索 FAQ 中的接口对接相关内容"
        ]
    )

    # 场景 5: 测试辅助系统
    await tester.run_test(
        test_name="场景5: 辅助系统 - 乐企",
        query="乐企通道如何配置？",
        expected_behaviors=[
            "识别为辅助系统问题（乐企）",
            "搜索 kb/产品与交付知识/11-常见问题/乐企问题/",
            "不需要询问产品线（乐企本身就是独立系统）"
        ]
    )

    # 场景 6: 测试订单系统（同义词）
    await tester.run_test(
        test_name="场景6: 辅助系统 - 订单系统（同义词EOP）",
        query="EOP 系统里怎么查看订单状态？",
        expected_behaviors=[
            "识别 EOP = 发票云订单系统",
            "搜索 kb/产品与交付知识/11-常见问题/发票云订单问题/",
            "正确处理同义词"
        ]
    )

    # 场景 7: 测试 RPA 通道（同义词）
    await tester.run_test(
        test_name="场景7: 辅助系统 - RPA通道",
        query="RPA通道配置失败怎么办？",
        expected_behaviors=[
            "识别 RPA通道 = 电子税局通道管理",
            "搜索相关文档",
            "正确处理同义词"
        ]
    )

    # 场景 8: 测试未找到答案的情况
    await tester.run_test(
        test_name="场景8: 未找到答案场景",
        query="如何使用发票云对接火星系统？",
        expected_behaviors=[
            "尝试搜索知识库",
            "未找到相关信息",
            '回复标准话术："抱歉，在发票云知识库没找到本答案，请联系发票云人工客服做支持。"'
        ]
    )

    # 场景 9: 测试产品同义词 - aws发票云
    await tester.run_test(
        test_name="场景9: 产品同义词 - aws发票云",
        query="aws发票云的影像功能在哪里？",
        expected_behaviors=[
            "识别 aws发票云 = 标准版",
            "识别功能模块：影像",
            "搜索标准版影像相关文档"
        ]
    )

    # 场景 10: 测试版本发布问题
    await tester.run_test(
        test_name="场景10: 版本发布信息",
        query="星瀚发票云 V8.0 有什么新功能？",
        expected_behaviors=[
            "识别产品：星瀚发票云",
            "识别为版本发布问题",
            "搜索 kb/产品与交付知识/01-交付赋能/产品知识/产品发版说明/星瀚发票云/V8.0/"
        ]
    )

    # 打印测试摘要
    tester.print_summary()


if __name__ == "__main__":
    print("""
╭──────────────────────────────────────────────────╮
│ 发票云客服 Skill 测试套件                        │
│ 测试 customer-service skill 的各种场景          │
╰──────────────────────────────────────────────────╯
    """)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(0)
