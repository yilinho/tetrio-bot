# Python Tetris bot for TETR.IO
This bot retrieves game data through color matching and calculates optimal moves using multiprocessing. It's optimized for back-to-back (b2b) moves, including T-spins and other advanced spins.

## Demo
https://youtu.be/nqyY3mnWVAE

## Usage
1. Adjust the following parameters in `bot.py` to match your screen's configuration:
    ```
    screen_resolution=(1920, 1080),
    board_top_left=(787, 220),
    board_bottom_right=(1133, 899),
    next_piece_xy_0=(1260, 300),
    next_piece_xy_4=(1260, 721),
    held_piece_xy=(691, 300),
    ```
2. Run the bot:
    ```
    python bot.py
    ```

## Game settings
- ARR 0ms
- DAS 40ms
- SDF max

## Disclaimer
Use this bot at your own discretion. Using it in multiplayer mode could result in your account and IP address being banned.
