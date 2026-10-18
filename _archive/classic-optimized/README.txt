Optimized Classic website snapshot

Captured before the academic website was promoted to the root.
Baseline Git commit: 79d855576353986ad328be370dd1d0174272e6ac.

Payload: index.html, all current assets/, images/optimized/ only, and every PDF
in files/. This includes the original vendor libraries and font licenses.
Excluded: .git, unoptimized images, academic/, unrelated root files, and non-PDF
files in files/ (including .DS_Store). No external files were copied.

To restore, copy this directory's payload into an empty website directory,
excluding README.txt and manifest.json. Relative local links remain self-contained.
The manifest records SHA-256 checksums and sizes for every payload file plus this
README. The manifest excludes itself. Keep this archive out of the public build.
