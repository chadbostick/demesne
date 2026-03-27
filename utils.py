import sys
import tty
import termios


def pause(message: str = "  ── Press Space/Enter to continue or Esc to quit ──", era: int = 0) -> None:
    """Block until the user presses Space, Enter, or Esc. Esc exits the process. Skips during era 1."""
    if era <= 1:
        return
    print(f"\n{message} ", end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    print()
    if ord(ch) == 27:   # Esc
        print("\nSimulation paused by user.")
        sys.exit(0)
