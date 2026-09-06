# Repository website

The landing page is plain HTML and CSS in `site/`. It has no build step, JavaScript runtime, third-party fonts, or tracking. Open `site/index.html` in a browser to preview it locally.

GitHub Pages is configured to deploy through Actions. The `Website` workflow publishes only `site/` when changes to that folder or its workflow reach `main`. It can also be run manually. The first publication requires pushing the website files and `.github/workflows/pages.yml`.

Configured address: https://wyrcan-io.github.io/playtestr/

Keep product claims aligned with the runner's tested behavior. The terminal output is an example and the failure diff is labeled as illustrative. When changing the layout, check a narrow mobile viewport and desktop, keyboard navigation, and in-page links.
