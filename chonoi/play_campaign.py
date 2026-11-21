
"""Chơi liên tục trên một cổng: Gather -> chuyển kho -> Quan."""

import sys
import time
import webbrowser
from pathlib import Path

from .contract import load_contract
from .errors import BadInput
from .inventory import read_inventory
from .live import LiveGame, LiveServer
from .scenario import load_scenario


def main():
    root = Path(__file__).resolve().parent.parent
    inventory_path = root / "campaign_inventory.json"

    server = None
    gather_game = None
    quan_game = None

    try:
        tuning = load_contract()["tuning"]

        # Giai đoạn 1: Gather
        gather_scenario = load_scenario(None, "gather", tuning)

        gather_game = LiveGame(
            "gather",
            tuning,
            gather_scenario,
            seed=1,
            inventory=None,
            inventory_out=str(inventory_path),
        )

        # Chỉ tạo duy nhất một server ở cổng 8000
        server = LiveServer(
            gather_game,
            host="127.0.0.1",
            port=8000
        )
        server.start()

        print("=== GATHER ===")
        print(f"Địa chỉ game: {server.url}")
        print("Chơi Gather đến khi kết thúc.")
        webbrowser.open_new_tab(server.url)

        # Chờ Gather kết thúc
        while True:
            with gather_game._lock:
                finished = gather_game.session.done
                reason = gather_game.session.sim.reason
                error = gather_game.error

            if error:
                raise RuntimeError(
                    "Gather gặp lỗi. Kiểm tra Terminal."
                )

            if finished:
                break

            time.sleep(0.2)

        if reason not in ("time", "docked", "fainted"):
            raise RuntimeError(
                f"Gather kết thúc bất thường: {reason}"
            )

        # Đọc kho nguyên liệu Gather vừa xuất
        inventory = read_inventory(str(inventory_path))

        print("\n=== KHO NGUYÊN LIỆU ===")
        print(inventory if inventory else "Kho trống")

        # Dừng mô phỏng Gather, giữ nguyên HTTP server
        gather_game.stop()

        # Giai đoạn 2: tạo game Quan với kho từ Gather
        quan_scenario = load_scenario(None, "quan", tuning)

        quan_game = LiveGame(
            "quan",
            tuning,
            quan_scenario,
            seed=1,
            inventory=inventory,
            inventory_out=None,
        )

        # Chuyển handler của server hiện tại sang game Quan
        server.httpd.RequestHandlerClass.game = quan_game
        server.game = quan_game

        quan_game.start()

        print("\n=== QUAN ===")
        print(f"Màn Quan đã sẵn sàng: {server.url}")
        print("Vẫn dùng cổng 8000. Nhấn Ctrl+C để thoát.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nĐang dừng game...")

    except (BadInput, OSError, RuntimeError) as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1

    finally:
        if server is not None:
            server.stop()
        else:
            if gather_game is not None:
                gather_game.stop()
            if quan_game is not None:
                quan_game.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
