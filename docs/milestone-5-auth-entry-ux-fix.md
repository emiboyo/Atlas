# Milestone 5 Authentication Entry UX Fix

## Defect

The public homepage exposed two ambiguous `Explore Atlas` controls but no
visible authentication entry. It did not distinguish signed-out visitors from
signed-in users, even though Clerk already protected the application and
provided account controls inside the authenticated navigation.

## Root cause

`apps/web/src/app/page.tsx` was static and did not use Clerk's `SignedIn`,
`SignedOut`, or `UserButton` boundary components. Its calls to action only
linked to page fragments, so they could neither start authentication nor open
the authenticated workspace.

## Files modified

- `apps/web/src/app/page.tsx`
- `apps/web/src/proxy.ts`
- `apps/web/src/test/home.test.tsx`
- `docs/milestone-5-auth-entry-ux-fix.md`

No protected layout, account navigation, permission, backend, database,
infrastructure, dependency, or governance file changed.

## Signed-out experience

The header exposes `Sign in` at `/sign-in` and `Get started` at `/sign-up` on
all viewport sizes. The hero exposes `Create account` at `/sign-up` and the
meaningful in-page `Explore the platform` architecture link. Neither a
dashboard link nor `UserButton` is rendered.

## Signed-in experience

The header exposes `Open dashboard` at `/app` and Clerk's `UserButton` with
`afterSignOutUrl="/"`. The hero exposes `Open Atlas dashboard` at `/app`.
Sign-in and account-creation actions are not rendered.

## Copy correction

The homepage no longer claims that users can invest from $10 or invest with
confidence through the current product. It now says:

> Explore strategies using transparent historical simulations.

The prior `$10` overview statistic is replaced with `Clear evidence`. A
prominent hero statement says that the experience is historical simulation
only, is not investment advice, and does not guarantee future performance.

## Security review

- Clerk's supported render-boundary components determine presentation only.
- The Next.js 16 proxy invokes `clerkMiddleware()` for application routes and
  excludes static assets. It deliberately does not call `auth.protect()`
  globally, so the homepage and Clerk sign-in/sign-up routes remain public.
- `/app` remains protected by the existing server layout and Clerk controls.
- Hidden controls are not treated as authorization.
- No secret key, mock identity, test authentication, or client-side
  authorization rule was added to production code.
- The existing `AccountNavigation`, permissions, and E2E Clerk harness are
  unchanged.
- If Clerk cannot establish an authenticated state, no application authority
  is granted; protected routes continue to enforce authentication server-side.

## Tests and totals

Homepage tests use a narrow module mock for Clerk render boundaries only. They
cover signed-out sign-in and account creation, absence of dashboard/account
controls, signed-in dashboard and account controls, absence of signed-out
actions, exact `/sign-in`, `/sign-up`, and `/app` routes, accessible names,
keyboard focus, authentication actions in primary/mobile-visible navigation,
and safe historical-research copy.

Final results:

- Homepage: 5 tests passed.
- Web: 52 tests passed across 5 files.
- Package total: 55 tests passed across 7 files (web 52, UI 2, shared 1).
- Chromium accessibility: 32 tests passed (16 desktop, 16 Pixel 7).
- Prettier: passed.
- ESLint: passed with zero warnings.
- TypeScript: passed.
- Next.js production build: passed; `/`, `/sign-in/[[...sign-in]]`,
  `/sign-up/[[...sign-up]]`, and `/app` are present, and the Next.js 16 proxy
  is included in the build.
- Docker web image: rebuilt with the ignored local Clerk configuration passed
  through the existing build-argument/runtime-environment wiring.
- Docker web container: healthy; logs report Next.js 16.2.11 ready on port
  3000, and `Invoke-WebRequest http://localhost:3000 -UseBasicParsing`
  returned HTTP 200.
- `git diff --check`: passed.

Existing React `act` messages in research tests remain non-failing test-harness
warnings and are unrelated to this change.

## Failed commands and corrections

1. The first inspection command contained an unterminated PowerShell quote.
   It was rerun with single-quoted ripgrep patterns and explicit path checks.
2. The first inspection rerun returned exit 1 after successfully printing the
   relevant files because two optional middleware paths did not exist. The
   repository file list was queried first and the actual layout/configuration
   files were then inspected.
3. The first combined focused gate passed 5 homepage tests and ESLint but
   TypeScript rejected plain `/sign-in` and `/sign-up` literals under Next.js
   typed routes. The existing repository convention was followed by importing
   `Route` and explicitly typing those known internal Clerk routes. The full
   typecheck and production build then passed.
4. The first Docker HTTP probe returned 500. Container logs showed that Clerk's
   publishable key was absent because Docker Compose does not automatically
   load app-scoped `apps/web/.env.local`. The file was confirmed ignored by
   Git and both Clerk variables were confirmed present without displaying
   their values. They were loaded into the build process, where the existing
   Compose configuration passes the publishable key as a build argument and
   the secret only as a server runtime variable. After rebuilding and
   recreating only the web service, the container became healthy and the
   homepage returned HTTP 200.

## Remaining limitations

The Clerk render-state unit test uses a deterministic component mock; it does
not replace real Clerk integration or server authorization. The existing
Chromium research accessibility harness does not exercise a live Clerk login,
and no production credentials were used. Production/public access and
Milestone 6 remain prohibited under current governance.

No deployment, production change, or Milestone 6 implementation was
performed.
