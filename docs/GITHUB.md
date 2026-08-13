# GitHub contributor hygiene

This project should show a single GitHub contributor: the repository owner.

## Do this when you commit and push

1. Commit locally with your own Git identity (already configured as `tah-rak` on this machine).
2. Do **not** add `Co-authored-by` trailers for Cursor, Copilot, Emergent, or any tool.
3. Push with your GitHub account only:

```bash
git add .
git status
git commit -m "Initial AutoHedge portfolio risk assistant"
git push -u origin main
```

4. After pushing, confirm on GitHub → Insights → Contributors that only your account appears.

## Avoid

- Committing from shared/bot accounts
- Force-adding co-author metadata
- Including Emergent/Cursor branding files (already ignored via `.gitignore`)
