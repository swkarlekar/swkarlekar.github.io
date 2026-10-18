Quarantined website snapshots

classic-optimized/ contains the optimized Classic website immediately before the
academic version became the main website. Its links and assets are self-contained.

original-79d8555/ contains the exact 64 tracked files from Git commit
79d855576353986ad328be370dd1d0174272e6ac, before the optimization work.

Each snapshot includes manifest.json with file sizes and SHA-256 checksums.
README.txt and manifest.json are archival metadata, not original website payload.
No .git directory or files outside the website workspace were copied.

Restore into an empty directory by copying the selected snapshot's contents,
including hidden files, except README.txt and manifest.json. Review the restored
site before deploying it. Historical dependencies are retained for preservation.
Keep _archive excluded from the public website build.
