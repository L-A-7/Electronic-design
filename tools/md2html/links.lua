-- Rewrite links to local .md files so they point to the generated .html pages.
function Link(el)
  if not el.target:match("^%a+://") then
    el.target = el.target:gsub("%.md$", ".html"):gsub("%.md#", ".html#")
  end
  return el
end
