import sys
import tty
import termios
import config


def pause(message: str = "  ── Press Space/Enter to continue or Esc to quit ──", era: int = 0, end_of_era: bool = False) -> None:
    """Block until the user presses Space, Enter, or Esc.

    Pauses are shown:
    - Always at end of era (end_of_era=True)
    - At all other points only if config.ALL_PAUSES is True and era > 1
    """
    if not config.ALL_PAUSES:
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
