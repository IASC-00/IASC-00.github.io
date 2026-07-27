# Portfolio Site

Live at https://iswain.dev — GitHub Pages, repo: IASC-00/IASC-00.github.io

## Deploy
```bash
git add -A && git commit -m "..." && git push
# Changes are live in ~60 seconds
```

## Key files
- `index.html` — main site (all sections: Hero, Projects, Services, Skills, About, Contact)
- `style.css` — all styles
- `script.js` — interactions, EmailJS, Formspree
- `intake.html` — 7-step pre-qual form
- `full-intake.html` — full intake after pre-qual
- `privacy-policy.html`, `terms.html` — legal pages
- `demos/` — static demo pages (automation.html, investment-committee.html)

## Payments
No Stripe links or deposit text on the public site. Payment handled via invoice or prior agreement only.

## Forms
- **Contact form**: Formspree mzdaldva (notifies Ian) + EmailJS auto-reply hybrid
- **EmailJS**: service_sq9pa4c, template_ri4lgfr, pubkey 0gqwG4ADip17Q2LRg, 200 req/mo
- **Calendly**: calendly.com/iswain-dev

## Content rules
- All project/service names are plain English — no tech brand names visible to clients
- Location: **Philadelphia, PA** — relocation complete. Hero, résumé and JSON-LD all say Philadelphia; `terms.html` governing law is Pennsylvania (Court of Common Pleas of Philadelphia County / E.D. Pa.) as of 2026-07-26. "United States" is correct only inside the JSON-LD `Country` field.
- Contact email: contact@iswain.dev (portfolio) / iswaindev@proton.me (resume/professional)

## Do not
- Add Google Analytics or Google Drive — never used
- Use paid hosting — GitHub Pages only
- Expose tech stack names in client-facing copy (say "AI-powered tool" not "Claude API")
- Make any GitHub repos public without auditing for personal info first

## Philadelphia move — DONE (closed 2026-07-26)
- Hero, résumé and structured data say Philadelphia. Done before 07-26.
- `terms.html` §9 governing law switched Virginia → Pennsylvania on 2026-07-26
  (Commonwealth of Pennsylvania · Court of Common Pleas of Philadelphia County ·
  E.D. Pa.), and the page's "Last updated" moved to that date.
- **The contract templates this checklist pointed at no longer exist.** The paths
  (`Desktop/ClaudeCode/Business/Project Contract Template.{md,html}`) are
  pre-migration and gone; a sweep of `ISDev_Projects`, `upwield` and `omaha` on
  2026-07-26 found no surviving template carrying a governing-law clause. If a
  client contract gets written, its venue clause has to be authored fresh — do not
  assume an old template is being reused and is already correct.
