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
- Location: "United States" until moved to Philadelphia (within ~2 months as of March 2026)
- Contact email: contact@iswain.dev (portfolio) / iswaindev@proton.me (resume/professional)

## Do not
- Add Google Analytics or Google Drive — never used
- Use paid hosting — GitHub Pages only
- Expose tech stack names in client-facing copy (say "AI-powered tool" not "Claude API")
- Make any GitHub repos public without auditing for personal info first

## When moved to Philly
- Update location in hero section
- Update governing law in contract templates (Virginia → Pennsylvania)
  - Desktop/ClaudeCode/Business/Project Contract Template.md — Section 11
  - Desktop/ClaudeCode/Business/Project Contract Template.html — Section 11
