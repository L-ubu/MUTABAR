# tests/test_renderer.py
from game.renderer import TextBuffer


def test_buffer_creates_with_size():
    buf = TextBuffer(cols=40, rows=30)
    assert buf.cols == 40
    assert buf.rows == 30


def test_write_text():
    buf = TextBuffer(cols=40, rows=30)
    buf.write(0, 0, "Hello")
    assert buf.get_char(0, 0) == "H"
    assert buf.get_char(4, 0) == "o"


def test_write_colored():
    buf = TextBuffer(cols=40, rows=30)
    buf.write(0, 0, "Hi", color=(255, 0, 0))
    assert buf.get_color(0, 0) == (255, 0, 0)


def test_clear():
    buf = TextBuffer(cols=40, rows=30)
    buf.write(0, 0, "Test")
    buf.clear()
    assert buf.get_char(0, 0) == " "


def test_draw_box():
    buf = TextBuffer(cols=40, rows=30)
    buf.draw_box(0, 0, 10, 5)
    assert buf.get_char(0, 0) == "┌"
    assert buf.get_char(9, 0) == "┐"
    assert buf.get_char(0, 4) == "└"
    assert buf.get_char(9, 4) == "┘"


def test_draw_hp_bar():
    buf = TextBuffer(cols=40, rows=30)
    buf.draw_hp_bar(0, 0, width=10, current=75, maximum=100)
    line = buf.get_line_text(0)
    assert "█" in line
    assert "░" in line


def test_write_wraps_at_boundary():
    buf = TextBuffer(cols=5, rows=2)
    buf.write(3, 0, "Hello")
    # Only "He" should fit on first line
    assert buf.get_char(3, 0) == "H"
    assert buf.get_char(4, 0) == "e"
