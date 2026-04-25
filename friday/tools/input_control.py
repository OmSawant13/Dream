"""
Input Control tools — control keyboard, mouse, and system actions.
Uses PyAutoGUI for cross-platform input simulation.
"""

import pyautogui
import webbrowser
import platform
import subprocess

# Disable fail-safe if the user is in a demo environment and might hit corners
pyautogui.FAILSAFE = False

def keyboard_type(text: str) -> str:
    """
    Types the specified text on the keyboard.
    """
    pyautogui.write(text, interval=0.1)
    return f"Typed '{text}' into the active window, boss."

def keyboard_press(key: str) -> str:
    """
    Presses a specific key (e.g., 'enter', 'tab', 'command', 'space').
    """
    # Map 'command' to 'gui' for pyautogui on Mac
    if platform.system() == "Darwin" and key.lower() == "command":
        key = "command"
    
    try:
        pyautogui.press(key)
        return f"Pressed the '{key}' key, boss."
    except Exception as e:
        return f"Keyboard error: {str(e)}"

def mouse_click(x: int = None, y: int = None) -> str:
    """
    Clicks the mouse. If x and y are provided, moves there first.
    """
    if x is not None and y is not None:
        pyautogui.click(x, y)
        return f"Clicked at coordinates ({x}, {y}), boss."
    else:
        pyautogui.click()
        return "Clicked at the current mouse position, boss."

def mouse_move(x: int, y: int) -> str:
    """
    Moves the mouse to specific coordinates.
    """
    pyautogui.moveTo(x, y, duration=0.5)
    return f"Moved mouse to ({x}, {y}), boss."

def search_google(query: str) -> str:
    """
    Opens the default browser and searches Google for the query.
    """
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Searching Google for '{query}' now, boss. I've opened your browser."

def register(mcp):
    @mcp.tool()
    def keyboard_type_tool(text: str) -> str:
        return keyboard_type(text)

    @mcp.tool()
    def keyboard_press_tool(key: str) -> str:
        return keyboard_press(key)

    @mcp.tool()
    def mouse_click_tool(x: int = None, y: int = None) -> str:
        return mouse_click(x, y)

    @mcp.tool()
    def mouse_move_tool(x: int, y: int) -> str:
        return mouse_move(x, y)

    @mcp.tool()
    def search_google_tool(query: str) -> str:
        return search_google(query)
