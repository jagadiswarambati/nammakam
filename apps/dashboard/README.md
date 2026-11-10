# Nammakam Dashboard

Next.js frontend application for viewing Nammakam safety-evaluation scorecards, episode transcripts, and verifiable evidence packs.

## Structure

- `src/app/`: Next.js App Router pages and layouts
  - `episodes/`: Episode playback and turn-by-turn drilldowns
  - `scorecards/`: Cross-language safety and parity matrices
  - `reports/`: Verifiable evidence packs and signature verification
- `src/components/`: UI components organized by domain
- `src/lib/`: API client and shared utility helpers
- `src/types/`: TypeScript interface definitions matching backend DTOs

## Development

```bash
npm install
npm run dev
```

