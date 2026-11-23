# Claude Code: start here (frontend session)

You are helping **Piyush**, who owns the frontend of Haq. The backend is built and owned
by Tijil. Before writing any code, read these files in order:

1. `CLAUDE.md` (repo root): rules for every session, including git and code style.
2. `docs/handoff/README.md`: the handoff index.
3. `docs/handoff/frontend-guide.md`: status, how to run, API rules, screens, UX rules.
4. `docs/handoff/api-codes.md`: every code the API sends and its params.
5. `docs/handoff/demo.md`: demo scenarios, sample photos, test logins.
6. `docs/haq-plan.pdf`: sections 1-5, 7, 8 and 9 only. Sections 6, 10 and 11 are for the
   backend.
7. `client/src/api/schema.d.ts`, `types.ts`, `client.ts`, `errors.ts`, `hooks.ts`,
   `downloads.ts`, then `client/src/lib/*.ts` and `client/src/i18n/index.ts`. Read these;
   don't rewrite them.

## Hard rules

- **Stay in your lane.** You may edit `client/src/app/**`, `client/src/components/**`,
  `client/src/features/**`, `client/src/lib/speech.ts`, `client/src/App.tsx`,
  `client/src/main.tsx`, `client/src/index.css` and the text in
  `client/src/i18n/locales/*.json`. You may also add client dependencies.
- **Do not edit** `server/**`, `client/src/api/**`, `client/src/lib/` (except `speech.ts`),
  `client/src/config/**` or `client/src/i18n/index.ts`. If you need a change there, stop
  and write it up for Piyush to send to Tijil.
- Never hand-edit `client/src/api/schema.d.ts`. After pulling backend changes, run
  `npm run types` in `client/`.
- Never run `git add`, `git commit` or `git push`. Read-only git is fine.
- Run the server locally with `STORAGE=memory` and `EXTRACTOR=mock` (see
  frontend-guide.md section 2). Docker is not needed.
- Before saying a screen is done, run `npm run lint`, `npm run typecheck` and
  `npm run test` in `client/`.

## Starter prompt (Piyush pastes this)

> Read docs/handoff/CLAUDE-START-HERE.md and every file it lists. The API client, hooks,
> formatters and i18n setup already exist; do not rewrite them. First, add Hindi and
> English text for the ten new reason codes in docs/handoff/api-codes.md. Then build the
> screens in the order of frontend-guide.md section 5, one at a time, starting with the
> app shell and UI kit. Mobile-first at 360px, Hindi default. Stop after each screen so
> I can review. Follow the comment rules strictly. Do not run any git write commands.
