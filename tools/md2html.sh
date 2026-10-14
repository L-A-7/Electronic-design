#!/usr/bin/env bash
# Render every Markdown file of the workspace to HTML in html/ (git-ignored).
# Markdown stays the source; re-run after edits. Open html/index.html in a browser.
# Usage: tools/md2html.sh            (all files)
#        tools/md2html.sh --open     (render, then open the index in the default browser)
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/html"
assets="$root/tools/md2html"
mkdir -p "$out"
cp "$assets/style.css" "$out/style.css"

mapfile -t files < <(cd "$root" && find . -name '*.md' -not -path './html/*' -not -path './.git/*' \
                      -not -path '*/output/*' -not -path '*/node_modules/*' | sed 's|^\./||' | sort)

# Copy images referenced by the docs (same relative paths, so Markdown image links keep working).
(cd "$root" && find . \( -name '*.png' -o -name '*.jpg' -o -name '*.svg' \) -path '*/docs/img/*' -not -path './html/*' \
    -exec cp --parents {} "$out/" \;)

count=0
for f in "${files[@]}"; do
    dest="$out/${f%.md}.html"
    mkdir -p "$(dirname "$dest")"
    # Relative path from this page back to html/ (for the stylesheet and the index link).
    depth=$(awk -F/ '{print NF-1}' <<<"$f")
    up="./"; [[ $depth -gt 0 ]] && up=$(printf '../%.0s' $(seq 1 "$depth"))
    title=$(grep -m1 '^# ' "$root/$f" | sed 's/^# //') || true
    pandoc "$root/$f" \
        --from gfm+smart --to html5 --standalone \
        --toc --toc-depth=3 \
        --lua-filter "$assets/links.lua" \
        --css "${up}style.css" \
        --metadata title="${title:-$f}" \
        --variable pagetitle="${title:-$f}" \
        --variable include-before="<nav class=\"crumbs\"><a href=\"${up}index.html\">Index</a> / ${f}</nav>" \
        --variable include-after="<footer>Generated from ${f} on $(date +%F)</footer>" \
        --template "$assets/template.html" \
        -o "$dest"
    count=$((count + 1))
done

# Index page listing every document by folder.
{
    echo "# Electronic design workspace"
    echo
    prev=""
    for f in "${files[@]}"; do
        dir=$(dirname "$f")
        if [[ "$dir" != "$prev" ]]; then
            echo; [[ "$dir" == "." ]] && echo "## (root)" || echo "## $dir"; echo
            prev="$dir"
        fi
        title=$(grep -m1 '^# ' "$root/$f" | sed 's/^# //') || true
        echo "- [${title:-$f}](${f%.md}.html) — \`$f\`"
    done
} | pandoc --from gfm --to html5 --standalone --css style.css \
        --metadata title="Electronic design workspace" \
        --template "$assets/template.html" -o "$out/index.html"

echo "Rendered $count files → $out/index.html"
[[ "${1:-}" == "--open" ]] && xdg-open "$out/index.html" >/dev/null 2>&1 &
exit 0
