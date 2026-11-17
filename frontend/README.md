# SwarmDining

SwarmDining lets restaurant guests order from their phones and helps the team coordinate the floor.

## Customer app

The installable customer-facing app lives in `apps/customer`.

```bash
corepack pnpm install
corepack pnpm dev
```

Open [http://localhost:3000](http://localhost:3000). The QR table placeholder is at `/t/4`.

## Build and checks

```bash
corepack pnpm build
corepack pnpm start
corepack pnpm lint
corepack pnpm typecheck
corepack pnpm format
```

The service worker is generated for production builds and disabled during development.
