# Knowledge Content

`docs/knowledge/**` is the business-owned content surface in `Hello-Docs`.
It is an intentional exception to the repository's one-way code-mirror rule.

## Ownership and editing

- Create, edit, rename, and remove knowledge-sharing content directly in a
  `Hello-Docs` content branch, then open a PR to `Hello-Docs/main`.
- Keep knowledge-content PRs under `docs/knowledge/**`. Do not mix changes to
  mirrored code, templates, workflows, `docs/publish/**`, or product-manual
  review files into the same PR.
- Do not copy this content into `auto-manual`. The engineering sync preserves
  the complete `Hello-Docs/main:docs/knowledge/**` tree.
- A knowledge-content change does not need an `auto-manual` PR or a preceding
  engineering sync. Once the content PR reaches `Hello-Docs/main`, the RTD
  project can publish it from that commit.

## AI sharing guide

- `ai-share/分享稿.md` is the editable prose source.
- `ai-share/00_打开分享.html` is the page served at `/ai-share/` and must carry
  the same approved wording as the prose source.
- Keep links and assets relative so the same directory works on RTD and in the
  downloadable offline bundle.
- Preserve the directory structure when adding, renaming, or removing linked
  examples, reference pages, styles, or images.

## Validation

- Review the diff and confirm every changed path is under `docs/knowledge/**`.
- Serve `docs/knowledge` locally and open `ai-share/00_打开分享.html`; check the
  navigation, reference links, images, narrow-screen layout, and print view.
- When prose changes, compare `分享稿.md` with the rendered HTML and confirm the
  headings, order, examples, and links stay aligned.

