from takopi.telegram.rich_message import (
    MAX_RICH_CHARS,
    build_input_rich_message,
    escape_raw_html,
    markdown_has_gfm_table,
    rich_limit_exceeded,
    should_use_rich_message,
)


TABLE = "| A | B |\n|---|---|\n| 1 | 2 |\n"


def test_markdown_has_gfm_table() -> None:
    assert markdown_has_gfm_table(TABLE)
    assert not markdown_has_gfm_table("no tables here")
    assert not markdown_has_gfm_table(f"```\n{TABLE}```\n")


def test_should_use_rich_message_auto() -> None:
    assert should_use_rich_message(TABLE, "auto")
    assert not should_use_rich_message(TABLE, "off")
    assert should_use_rich_message("hello", "always")
    assert not should_use_rich_message("   ", "always")


def test_should_use_rich_message_ignores_code_headings() -> None:
    filler = "word " * 120
    assert should_use_rich_message(f"## Results\n\n{filler}", "auto")
    assert not should_use_rich_message(
        f"```sh\n## not a heading\n```\n\n{filler}", "auto"
    )


def test_rich_limit_exceeded() -> None:
    assert rich_limit_exceeded(TABLE) is None
    wide = "|" + "|".join(f" c{i} " for i in range(25)) + "|"
    assert rich_limit_exceeded(wide) == "columns"
    assert rich_limit_exceeded("x" * (MAX_RICH_CHARS + 1)) == "chars"
    assert rich_limit_exceeded("\n\n".join(f"para {i}" for i in range(600))) == "blocks"


def test_build_input_rich_message_escapes_html_outside_code() -> None:
    markdown = "use `Vec<T>`\n\n```rust\nlet x: Vec<T> = vec![];\n```\n\n<b>x</b>\n"
    payload = build_input_rich_message(markdown)

    assert "`Vec<T>`" in payload["markdown"]
    assert "let x: Vec<T>" in payload["markdown"]
    assert "&lt;b>x&lt;/b>" in payload["markdown"]
    assert escape_raw_html("> quoted\n") == "> quoted\n"
