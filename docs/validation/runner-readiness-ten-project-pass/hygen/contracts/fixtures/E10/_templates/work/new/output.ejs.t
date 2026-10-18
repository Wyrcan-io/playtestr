---
to: "document.txt"
inject: true
eof_last: false
after: "^header$"
skip_if: "already-present"
---
new <%= message %>
