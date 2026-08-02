"""Application entry point for the TETR.IO bot.

This module owns configuration loading, screen calibration, command-line
arguments, and startup/shutdown. The gameplay and screen-processing logic is
implemented by :class:`tetrio.TetrioBot`.
"""

import argparse
import json
import os

import keyboard
import pyautogui
import time

from constants import DEFAULT_MOVE_DELAY_MS, DEFAULT_ACTION_DELAY_MS, DEFAULT_DELAY_VARIANCE_PERCENT, DEFAULT_PRUNING_MOVES, DEFAULT_PRUNING_BREADTH, DEFAULT_MP
from tetrio import TetrioBot

CONFIG_FILE = "config.json"


def load_config():
    """Load configuration from config.json if it exists.
    Applies default values for any missing delay settings."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            # Apply defaults for delay settings if not present
            if 'move_delay_ms' not in config:
                config['move_delay_ms'] = DEFAULT_MOVE_DELAY_MS
            if 'action_delay_ms' not in config:
                config['action_delay_ms'] = DEFAULT_ACTION_DELAY_MS
            if 'delay_variance_percent' not in config:
                config['delay_variance_percent'] = DEFAULT_DELAY_VARIANCE_PERCENT
            return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file: {e}")
    return None


def save_config(config):
    """Save configuration to config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"\nConfiguration saved to {CONFIG_FILE}")


def run_calibration_wizard():
    """
    Interactive calibration wizard to capture screen coordinates for TetrioBot.
    Guides the user through clicking on specific positions on the game screen.
    """
    print("\n" + "=" * 60)
    print("       TETRIOBOT CALIBRATION WIZARD")
    print("=" * 60)
    print("\nThis wizard will help you configure the screen coordinates")
    print("for the TetrioBot. You will be guided through 5 steps.\n")
    print("INSTRUCTIONS:")
    print("  1. Position your TETR.IO game window where you want it")
    print("  2. For each step, move your mouse to the indicated position")
    print("  3. Press '=' key to capture the current mouse position")
    print("  4. Press 'Escape' to cancel calibration at any time\n")
    
    # Detect screen offset for multi-monitor setups
    screens = pyautogui.size()
    print(f"Detected primary screen resolution: {screens[0]}x{screens[1]}")
    
    # Try to detect monitor offset
    # pyautogui.position() returns absolute coordinates across all monitors
    print("\nTo detect your monitor offset, please move your mouse to the")
    print("TOP-LEFT corner of your TETR.IO game window and press '='")
    print("(This helps with multi-monitor setups)\n")
    
    steps = [
        ("BOARD TOP-LEFT", "Click on the TOP-LEFT corner of the game board (where pieces stack)"),
        ("BOARD BOTTOM-RIGHT", "Click on the BOTTOM-RIGHT corner of the game board"),
        ("NEXT PIECE #1", "Click on the CENTER of the FIRST next piece (top of next queue)"),
        ("NEXT PIECE #5", "Click on the CENTER of the FIFTH next piece (bottom of next queue)"),
        ("HELD PIECE", "Click on the CENTER of the HELD piece display"),
    ]
    
    captured_positions = []
    
    for i, (name, instruction) in enumerate(steps, 1):
        print(f"\n--- Step {i}/5: {name} ---")
        print(f"  {instruction}")
        print("  >> Move your mouse to the position and press '=' to capture")
        print("  >> Press 'Escape' to cancel")
        
        # Wait for keypress
        while True:
            event = keyboard.read_event(suppress=False)
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == '=':
                    pos = pyautogui.position()
                    captured_positions.append(pos)
                    print(f"  ✓ Captured: ({pos[0]}, {pos[1]})")
                    time.sleep(0.2)  # Small delay to prevent double-capture
                    break
                elif event.name == 'escape':
                    print("\n\nCalibration cancelled by user.")
                    return None
    
    # Process captured positions
    board_top_left = captured_positions[0]
    board_bottom_right = captured_positions[1]
    next_piece_0 = captured_positions[2]
    next_piece_4 = captured_positions[3]
    held_piece = captured_positions[4]
    
    # Calculate screen offset (assume primary monitor if board is on it)
    # Use the top-left of the board to determine which monitor
    screen_offset = (0, 0)
    
    # Check if position suggests a different monitor
    primary_width, primary_height = pyautogui.size()
    if board_top_left[0] < 0:
        # Left of primary monitor
        screen_offset = (board_top_left[0] - (board_top_left[0] % primary_width), 0)
    elif board_top_left[0] >= primary_width:
        # Right of primary monitor
        screen_offset = (primary_width, 0)
    
    # Ask user about screen offset
    print(f"\n--- Screen Offset Detection ---")
    print(f"  Detected board position: ({board_top_left[0]}, {board_top_left[1]})")
    print(f"  Suggested screen_offset: {screen_offset}")
    print(f"\n  If your game is on a secondary monitor, you may need to adjust this.")
    print(f"  Common values: (0, 0) for primary, (-1920, 0) for left monitor,")
    print(f"  (1920, 0) for right monitor")
    
    # Get screen resolution (use the board area to estimate)
    screen_resolution = (primary_width, primary_height)
    
    # Prompt for delay settings
    print(f"\n--- Step 6/6: DELAY SETTINGS ---")
    print("  Configure delays to make inputs appear more human-like.")
    print("  This helps avoid anti-cheat detection.\n")
    
    print(f"  Move Delay: Delay between each keypress (default: {DEFAULT_MOVE_DELAY_MS}ms)")
    move_delay_input = input(f"  Enter move delay in ms (or press Enter for default): ").strip()
    move_delay_ms = int(move_delay_input) if move_delay_input else DEFAULT_MOVE_DELAY_MS
    
    print(f"\n  Action Delay: Delay after actions like hold/rotate (default: {DEFAULT_ACTION_DELAY_MS}ms)")
    action_delay_input = input(f"  Enter action delay in ms (or press Enter for default): ").strip()
    action_delay_ms = int(action_delay_input) if action_delay_input else DEFAULT_ACTION_DELAY_MS
    
    print(f"\n  Delay Variance: Random variance percentage (default: {DEFAULT_DELAY_VARIANCE_PERCENT}%)")
    print("  Example: 20% variance on 30ms = delays between 24ms-36ms")
    variance_input = input(f"  Enter variance percentage (or press Enter for default): ").strip()
    delay_variance_percent = int(variance_input) if variance_input else DEFAULT_DELAY_VARIANCE_PERCENT

    print(f"\n  Pruning Moves: Number of candidate moves to keep (default: {DEFAULT_PRUNING_MOVES})")
    pruning_moves_input = input(f"  Enter pruning moves (or press Enter for default): ").strip()
    pruning_moves = int(pruning_moves_input) if pruning_moves_input else DEFAULT_PRUNING_MOVES

    print(f"\n  Pruning Breadth: Number of future results to keep (default: {DEFAULT_PRUNING_BREADTH})")
    pruning_breadth_input = input(f"  Enter pruning breadth (or press Enter for default): ").strip()
    pruning_breadth = int(pruning_breadth_input) if pruning_breadth_input else DEFAULT_PRUNING_BREADTH

    print(f"\n  Multiprocessing Workers (default: {DEFAULT_MP})")
    mp_input = input(f"  Enter multiprocessing workers (or press Enter for default): ").strip()
    mp = int(mp_input) if mp_input else DEFAULT_MP
    
    # Build the configuration
    config = {
        "screen_offset": list(screen_offset),
        "screen_resolution": list(screen_resolution),
        "board_top_left": list(board_top_left),
        "board_bottom_right": list(board_bottom_right),
        "next_piece_xy_0": list(next_piece_0),
        "next_piece_xy_4": list(next_piece_4),
        "held_piece_xy": list(held_piece),
        "move_delay_ms": move_delay_ms,
        "action_delay_ms": action_delay_ms,
        "delay_variance_percent": delay_variance_percent,
        "pruning_moves": pruning_moves,
        "pruning_breadth": pruning_breadth,
        "mp": mp,
    }
    
    # Display results
    print("\n" + "=" * 60)
    print("       CALIBRATION COMPLETE!")
    print("=" * 60)
    print("\nCaptured coordinates:\n")
    print(f"  Board Top-Left:     ({board_top_left[0]}, {board_top_left[1]})")
    print(f"  Board Bottom-Right: ({board_bottom_right[0]}, {board_bottom_right[1]})")
    print(f"  Next Piece #1:      ({next_piece_0[0]}, {next_piece_0[1]})")
    print(f"  Next Piece #5:      ({next_piece_4[0]}, {next_piece_4[1]})")
    print(f"  Held Piece:         ({held_piece[0]}, {held_piece[1]})")
    print(f"\nDelay settings:")
    print(f"  Move Delay:         {move_delay_ms}ms")
    print(f"  Action Delay:       {action_delay_ms}ms")
    print(f"  Delay Variance:     {delay_variance_percent}%")
    
    print("\n" + "-" * 60)
    print("COPY-PASTE READY CONFIGURATION:")
    print("-" * 60)
    print(f"""
bot = TetrioBot(
    screen_offset={tuple(screen_offset)},
    screen_resolution={tuple(screen_resolution)},
    board_top_left={tuple(board_top_left)},
    board_bottom_right={tuple(board_bottom_right)},
    next_piece_xy_0={tuple(next_piece_0)},
    next_piece_xy_4={tuple(next_piece_4)},
    held_piece_xy={tuple(held_piece)},
    pruning_moves={pruning_moves},
    pruning_breadth={pruning_breadth},
    mp={mp},
    move_delay_ms={move_delay_ms},
    action_delay_ms={action_delay_ms},
    delay_variance_percent={delay_variance_percent}
)
""")
    
    # Save to config file
    save_config(config)
    
    print("\nYou can also run the bot with the saved config using:")
    print("  python bot.py --use-config\n")
    
    return config


def main():
    parser = argparse.ArgumentParser(description='TetrioBot - An AI player for TETR.IO')
    parser.add_argument('--calibrate', action='store_true',
                        help='Run the calibration wizard to configure screen coordinates')
    parser.add_argument('--use-config', action='store_true',
                        help='Use saved configuration from config.json')
    parser.add_argument('--pruning-moves', type=int, default=None,
                        help='Override pruning moves from config')
    parser.add_argument('--pruning-breadth', type=int, default=None,
                        help='Override pruning breadth from config')
    parser.add_argument('--mp', type=int, default=None,
                        help='Override multiprocessing workers from config')
    parser.add_argument('--delay', type=int, default=None,
                        help='Override move delay in milliseconds (e.g., --delay 50)')
    parser.add_argument('--action-delay', type=int, default=None,
                        help='Override action delay in milliseconds')
    parser.add_argument('--delay-variance', type=int, default=None,
                        help='Override delay variance percentage')
    
    args = parser.parse_args()
    
    if args.calibrate:
        run_calibration_wizard()
        return
    
    # Load configuration
    config = load_config()
    if config is None:
        print("Error: No config.json found. Run with --calibrate first.")
        return
        
    # Apply CLI overrides for delay settings
    move_delay_ms = args.delay if args.delay is not None else config.get('move_delay_ms', DEFAULT_MOVE_DELAY_MS)
    action_delay_ms = args.action_delay if args.action_delay is not None else config.get('action_delay_ms', DEFAULT_ACTION_DELAY_MS)
    delay_variance_percent = args.delay_variance if args.delay_variance is not None else config.get('delay_variance_percent', DEFAULT_DELAY_VARIANCE_PERCENT)

    print(f"Loaded configuration from {CONFIG_FILE}")
    print(f"Delay settings: move={move_delay_ms}ms, action={action_delay_ms}ms, variance={delay_variance_percent}%")
    bot = TetrioBot(
        screen_offset=tuple(config['screen_offset']),
        screen_resolution=tuple(config['screen_resolution']),
        board_top_left=tuple(config['board_top_left']),
        board_bottom_right=tuple(config['board_bottom_right']),
        next_piece_xy_0=tuple(config['next_piece_xy_0']),
        next_piece_xy_4=tuple(config['next_piece_xy_4']),
        held_piece_xy=tuple(config['held_piece_xy']),
        pruning_moves=args.pruning_moves if args.pruning_moves is not None else config.get('pruning_moves', DEFAULT_PRUNING_MOVES),
        pruning_breadth=args.pruning_breadth if args.pruning_breadth is not None else config.get('pruning_breadth', DEFAULT_PRUNING_BREADTH),
        mp=args.mp if args.mp is not None else config.get('mp', DEFAULT_MP),
        move_delay_ms=move_delay_ms,
        action_delay_ms=action_delay_ms,
        delay_variance_percent=delay_variance_percent
    )
    time.sleep(1)
    bot.run()


if __name__ == "__main__":
    main()
