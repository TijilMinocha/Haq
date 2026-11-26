# covexcode notes

Facts about this repo that are easy to rediscover the hard way.

- **Every `.py` file is CRLF.** `write_file` writes LF and `upload`ed tools keep LF, so after
  creating or rewriting a file convert it back: `uv run ruff format` does *not* do it
  (`line-ending = "auto"` means it preserves whatever the file already has). `ruff format
  --check .` will not catch LF files, but a CRLF-only diff shows up in every later review.
- **RUF001 flags the Devanagari digit zero `०` in string literals** (it is confusable with a
  Latin `o`/`0`). Write Hindi-digit test pages by translating ASCII digits instead:
  `str.maketrans("0123456789", "".join(chr(0x0966 + i) for i in range(10)))`.
- Edits to a CRLF file fail with "old_string was not found" because `edit_file` matches bytes;
  convert to LF, edit, convert back.
