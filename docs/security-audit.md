# Security audit of the backend API

The audit covers every endpoint in `server/app/api/v1/`, the access checks in
`server/app/api/deps.py`, the services behind them and the HTTP layer. Haq holds Aadhaar
numbers, bank details and death records, so each item was checked like an attacker would,
and each verdict is backed by a test or by the file named in the evidence column.

`safe` means the behaviour already held and a regression test now pins it. `fixed` means
this audit changed the code and the named test fails without the change. `accepted risk`
means the behaviour is deliberate and the cost of removing it is higher than the risk.

| # | Item | Verdict | Evidence | Note |
| --- | --- | --- | --- | --- |
| 1 | A case token for case A on case B | safe | `tests/api/test_access_control.py::test_case_token_does_not_open_another_case` | 401 `invalid_token` on all seven case routes, and the other case is unchanged afterwards. |
| 2 | An operator seeing or editing another operator's cases | safe | `test_operator_cannot_open_a_case_they_do_not_own`, `test_operators_only_list_their_own_cases`, `test_a_case_made_without_an_operator_belongs_to_nobody` | 403 on a foreign case; `GET /operator/cases` returns only the caller's own, and a case created without an operator has no owner to match. |
| 3 | A document id from one case used under another case's URL | safe | `test_document_id_from_one_case_is_not_found_under_another` | 404 `document_not_found` for both PATCH and DELETE; the document stays in its own case. |
| 4 | Every route that should need auth | safe | `test_the_route_list_matches_the_documented_guards`, `test_every_case_route_needs_credentials`, `test_operator_routes_need_an_operator_token`, `test_a_bad_bearer_fails_closed_on_a_public_route` | The public/guarded route table lives in the test and is compared with the OpenAPI schema, so a new route cannot ship unclassified. |
| 5 | PIN resume guessing | accepted risk | `test_wrong_pin_locks_after_five_attempts`, `test_guesses_spread_across_many_case_codes_are_throttled_per_ip`, `test_a_correct_pin_clears_the_counters`, `app/services/case_service.py:112` | Counted per case code and per IP, and a correct PIN resets both; the per-IP budget is shared by everyone behind one address (see accepted risks). |
| 6 | Case tokens and PINs stored hashed, compared in constant time | fixed | `test_case_token_and_pin_are_stored_hashed`, `app/core/security.py::token_matches` | The test proves the PIN is argon2 and the token is only ever stored as a SHA-256 digest; the comparison loops over every digest with `hmac.compare_digest` and never exits early (code, not test). |
| 7 | Operator JWT | safe | `test_unsigned_and_foreign_algorithm_tokens_are_rejected`, `test_an_expired_operator_token_is_rejected`, `test_operator_token_expires_after_the_configured_hours`, `tests/unit/test_production_settings.py::test_unsafe_production_settings_refuse_to_start` | Only HS256 is accepted, so `none` and RS/HS confusion fail; `exp` is enforced; production refuses a default or short `JWT_SECRET`. |
| 8 | Error messages revealing whether a case code exists | safe | `test_a_wrong_pin_and_an_unknown_code_are_indistinguishable`, `test_an_unknown_case_code_still_costs_a_password_hash`, `test_an_unknown_email_still_costs_a_password_hash` | A wrong PIN and an unknown code return the same 401 body, and an unknown code or email still pays for an argon2 verify against a decoy hash. |
| 9 | Upload size, content type checks and bombs | fixed | `test_the_content_type_is_decided_by_the_bytes_not_the_header`, `test_a_zero_byte_file_is_refused`, `test_a_png_bomb_is_refused_before_it_is_decoded`, `test_a_file_too_large_for_the_setting_is_refused`, `app/services/document_service.py::read_upload` | Type comes from the magic bytes (`sniffing.py`), not the header; an empty file and a 50-megapixel-plus PNG are refused, and a declared length over the limit is a 413 before the body is read. Without a declared length, `read_upload` still stops once the body passes the limit. |
| 10 | Uploaded bytes never stored | safe | `test_uploaded_bytes_are_never_kept` | A marker inside the upload is absent from the response and from the stored case; only the extracted, masked fields survive. |
| 11 | Aadhaar masked to the last 4 digits | fixed | `test_extracted_numbers_are_masked_before_they_are_stored`, `test_a_typed_aadhaar_is_masked_on_the_way_in`, `test_an_aadhaar_number_cannot_be_stored_whole`, `test_logs_carry_no_tokens_pins_or_personal_data`, `app/schemas/document.py:43` | Masked on OCR text before parsing and again on anything stored, including typed corrections; the stored field is pattern-pinned to `XXXX-XXXX-\d{4}`, no PDF layout prints an Aadhaar, and the 422 body carries only the field path and message, never the rejected value. |
| 12 | Request logs without bodies, tokens, PINs or headers | safe | `test_logs_carry_no_tokens_pins_or_personal_data`, `test_the_access_log_never_contains_the_query_string` | The access log records method, path, status and duration only. Both tests had to be corrected in this pass: the case id in the path is not a secret, and the query-string test was catching httpx's own client log rather than `haq.access`. |
| 13 | CORS limited to the configured origins | fixed | `test_only_configured_origins_are_allowed`, `test_a_wildcard_origin_is_refused_by_settings`, `app/core/config.py:52` | Settings refuse `*` outright, no credentials are allowed, and an unlisted origin gets no CORS header even on a preflight. |
| 14 | Security headers on every response, including errors | safe | `test_security_headers_are_on_every_response`, `test_refusals_from_the_middleware_carry_headers_too` | Nosniff, DENY framing, no-referrer, HSTS and `no-store` are set on success, on 401/404/415/422 and on the middleware's own 413 and 429. |
| 15 | Rate limits on login, case create, resume and upload | safe | `test_the_costly_routes_are_rate_limited`, `test_rate_limit_returns_429_with_retry_after`, `app/core/rate_limit.py` | Each of the four routes returns 429 `too_many_attempts` with `Retry-After` once its per-minute budget is spent. |
| 16 | Request ids not reflected unsanitised | safe | `test_an_incoming_request_id_cannot_break_the_response`, `test_a_garbage_request_id_still_gives_every_response_an_id` | Only `^[A-Za-z0-9._-]{1,64}$` (full match, so a trailing newline fails) is echoed; anything else is replaced by a fresh uuid. |

## Accepted risks

- **Per-IP resume lockout in a shared CSC centre.** The per-IP counter is four times the
  per-code budget, so a bot walking case codes cannot buy guesses by spreading them out.
  The price is that a busy Common Service Centre, where many families share one IP, can
  briefly lock every one of them out of resume for a minute after a handful of mistyped
  PINs. A per-IP limit is the only thing that stops a spread-out guessing run over a
  single instance without a paid WAF, and the cost of the risk is a short wait, so it is
  accepted.
- **The limiter and the attempt stores are in-process.** Several app instances would each
  allow the full rate. The deployment runs a single free instance, and the comment in
  `app/core/rate_limit.py` records that trade-off.
- **An unknown case id is a 404 while a wrong token is a 401.** That tells a caller that a
  random `c_` id is not in use. Case ids are eight random hex characters, so this reveals
  nothing about a real case and cannot be used to enumerate them. The case *code* path,
  which is the one a person types, gives nothing away (item 8).
