# covexcode notes

Facts about this repo that are easy to rediscover the hard way.

- **Not every `.py` file is CRLF — check before converting.** The audit's files under
  `server/` are LF (checked: `app/core/middleware.py`, `app/services/auth_service.py`,
  `app/api/v1/cases.py`, `tests/api/test_http_hardening.py`, `test_uploads.py`,
  `test_access_control.py`), so `edit_file` works on them directly. Where a file *is* CRLF,
  `write_file` writes LF and `upload`ed tools keep LF, and `uv run ruff format` does *not*
  fix it (`line-ending = "auto"` preserves whatever the file already has); `ruff format
  --check .` will not catch LF files either, but a CRLF-only diff shows up in every later
  review. To test a file: `b"\r\n" in path.read_bytes()`.
- **RUF001 flags the Devanagari digit zero `०` in string literals** (it is confusable with a
  Latin `o`/`0`). Write Hindi-digit test pages by translating ASCII digits instead:
  `str.maketrans("0123456789", "".join(chr(0x0966 + i) for i in range(10)))`.
- Edits to a CRLF file fail with "old_string was not found" because `edit_file` matches bytes;
  convert to LF, edit, convert back.
- **Log assertions in `server/tests` must attach to the `haq.access` logger, not the root
  logger.** `httpx` logs the full URL of every request the test client makes, so a root
  capture sees query strings and URL path ids and fails a test that is really about the
  server's own access line.
