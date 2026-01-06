#!/usr/bin/env python3
"""
Claude Code CLI 多轮对话 Demo

使用 CLI -p 模式实现多轮对话，支持自动保存 session_id
"""

import subprocess
import json
import sys
from typing import Optional, Dict, Any


class ClaudeCliChat:
    """Claude Code CLI 多轮对话管理器"""

    def __init__(
        self,
        allowed_tools: Optional[list] = None,
        skip_permissions: bool = False,
        cwd: Optional[str] = None
    ):
        """
        初始化聊天管理器

        Args:
            allowed_tools: 允许使用的工具列表，如 ["Read", "Grep", "Glob", "Bash"]
            skip_permissions: 是否跳过权限确认
            cwd: 工作目录
        """
        self.session_id: Optional[str] = None
        self.allowed_tools = allowed_tools or ["Read", "Grep", "Glob", "Bash", "WebFetch"]
        self.skip_permissions = skip_permissions
        self.cwd = cwd
        self.turn_count = 0

    def _build_command(self, prompt: str) -> list:
        """构建 claude CLI 命令"""
        cmd = ["claude", "-p", prompt, "--output-format", "json"]

        # 添加允许的工具
        if self.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(self.allowed_tools)])

        # 跳过权限确认
        if self.skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        # 如果有 session_id，使用 resume
        if self.session_id:
            cmd.extend(["--resume", self.session_id])

        return cmd

    def query(self, prompt: str) -> Dict[str, Any]:
        """
        发送查询到 Claude Code CLI

        Args:
            prompt: 用户输入的问题

        Returns:
            解析后的 JSON 响应
        """
        cmd = self._build_command(prompt)

        print(f"\n[执行命令] {' '.join(cmd)}")
        print("-" * 80)

        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.cwd,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                print(f"❌ 命令执行失败 (exit code: {result.returncode})")
                print(f"错误信息: {result.stderr}")
                return {
                    "error": result.stderr,
                    "exit_code": result.returncode
                }

            # 解析 JSON 输出
            try:
                response = json.loads(result.stdout)

                # 提取 session_id（首次查询时）
                if not self.session_id and "session_id" in response:
                    self.session_id = response["session_id"]
                    print(f"✅ 会话已创建: {self.session_id}\n")

                return response

            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失败: {e}")
                print(f"原始输出:\n{result.stdout}")
                return {
                    "error": "JSON parse error",
                    "raw_output": result.stdout
                }

        except subprocess.TimeoutExpired:
            print("❌ 命令执行超时（超过5分钟）")
            return {"error": "timeout"}
        except Exception as e:
            print(f"❌ 执行异常: {e}")
            return {"error": str(e)}

    def print_response(self, response: Dict[str, Any]):
        """格式化打印响应"""
        if "error" in response:
            print(f"\n❌ 错误: {response['error']}")
            return

        # 打印结果
        if "result" in response:
            print(f"\n🤖 Claude 回复:\n")
            print(response["result"])

        # 打印其他有用信息
        if "usage" in response:
            usage = response["usage"]
            print(f"\n📊 Token 使用: 输入 {usage.get('input_tokens', 0)} | 输出 {usage.get('output_tokens', 0)}")

        print("\n" + "=" * 80)

    def start_repl(self):
        """启动交互式 REPL"""
        print("=" * 80)
        print("Claude Code CLI 多轮对话 Demo")
        print("=" * 80)
        print(f"允许的工具: {', '.join(self.allowed_tools)}")
        print(f"跳过权限确认: {'是' if self.skip_permissions else '否'}")
        print(f"工作目录: {self.cwd or '当前目录'}")
        print("\n命令:")
        print("  - 输入问题开始对话")
        print("  - 'exit' 或 'quit' 退出")
        print("  - 'reset' 重置会话（开始新对话）")
        print("  - 'session' 查看当前 session_id")
        print("=" * 80)

        while True:
            try:
                # 获取用户输入
                self.turn_count += 1
                user_input = input(f"\n[轮次 {self.turn_count}] 你: ").strip()

                if not user_input:
                    self.turn_count -= 1
                    continue

                # 处理特殊命令
                if user_input.lower() in ["exit", "quit"]:
                    print("\n👋 再见！")
                    break

                if user_input.lower() == "reset":
                    self.session_id = None
                    self.turn_count = 0
                    print("✅ 会话已重置，将开始新对话")
                    continue

                if user_input.lower() == "session":
                    if self.session_id:
                        print(f"当前 session_id: {self.session_id}")
                    else:
                        print("尚未创建会话")
                    self.turn_count -= 1
                    continue

                # 发送查询
                response = self.query(user_input)
                self.print_response(response)

            except KeyboardInterrupt:
                print("\n\n👋 检测到 Ctrl+C，退出...")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                import traceback
                traceback.print_exc()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Code CLI 多轮对话 Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基础使用
  python claude_cli_demo.py

  # 跳过权限确认（自动批准所有工具使用）
  python claude_cli_demo.py --skip-permissions

  # 指定工作目录
  python claude_cli_demo.py --cwd /path/to/project

  # 自定义允许的工具
  python claude_cli_demo.py --tools "Read,Grep,Bash"
        """
    )

    parser.add_argument(
        "--skip-permissions",
        action="store_true",
        help="跳过权限确认，自动批准所有工具使用（危险！）"
    )

    parser.add_argument(
        "--tools",
        type=str,
        default="Read,Grep,Glob,Bash,WebFetch",
        help="允许使用的工具列表（逗号分隔），默认: Read,Grep,Glob,Bash,WebFetch"
    )

    parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="工作目录路径"
    )

    args = parser.parse_args()

    # 解析工具列表
    tools = [t.strip() for t in args.tools.split(",") if t.strip()]

    # 创建聊天实例
    chat = ClaudeCliChat(
        allowed_tools=tools,
        skip_permissions=args.skip_permissions,
        cwd=args.cwd
    )

    # 启动 REPL
    chat.start_repl()


if __name__ == "__main__":
    main()
