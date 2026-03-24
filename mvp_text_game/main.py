from engine import GameEngine
from llm_client import MiniMaxLLMClient
from state_factory import create_initial_state


def create_llm_client():
    return MiniMaxLLMClient()


def print_intro() -> None:
    print("=== 文字游戏 MVP ===")
    print("输入 A / B / C 进行选择，输入 q 退出。")


def main() -> None:
    state = create_initial_state()
    engine = GameEngine(create_llm_client())

    print_intro()
    print(f"\n初始场景: {state.scene}")
    print(f"初始剧情: {state.story_log[-1]}")
    print("初始选项:")
    for c in state.choices:
        print(f"{c.id}. {c.text}")

    while True:
        user_input = input("\n你的选择(A/B/C, q退出): ").strip().upper()
        if user_input == "Q":
            print("游戏结束。")
            break

        try:
            turn_output = engine.play_turn(state, user_input)
            print(turn_output)
        except Exception as exc:  # noqa: BLE001
            print(f"处理失败: {exc}")


if __name__ == "__main__":
    main()
