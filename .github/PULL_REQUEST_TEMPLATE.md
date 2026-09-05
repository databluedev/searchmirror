## What this changes

<!-- One or two sentences. What is different after this is merged. -->

## Why

<!-- The problem it solves. Link the issue if there is one: Fixes #123 -->

## What I verified

<!-- Be specific and honest. "Builds and the suite passes" is useful.
     Claiming more than you checked is not. Say what you did NOT test. -->

- [ ] `python -m pytest tests -q` passes against a running stack
- [ ] `docker compose exec -T backend python manage.py check` is clean
- [ ] `docker compose exec -T engine python manage.py check` is clean
- [ ] `docker compose exec -T app npm run build` succeeds (if the frontend changed)
- [ ] I clicked through the screens this touches

**Not verified:**

<!-- e.g. "did not test reports; no GSC account to test against" -->

## Checklist

- [ ] I did not weaken or delete a test to make the suite pass
- [ ] No provider credits were spent in a test (Rank, Refresh and Generate cost money)
- [ ] A new setting is documented in `.env.example` and `docs/CONFIGURATION.md`
- [ ] A new column on `keyword` or `group` is declared in **both** ORMs — see CLAUDE.md
- [ ] No hardcoded colour; tokens come from `_tokens.scss` (`docs/DESIGN.md`)
- [ ] No secrets, keys, or personal data in the diff
