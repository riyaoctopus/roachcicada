# Sources

Documentation compiled 16 August 2026. Listed roughly in order of authority (primary developer sources first).

## Primary (developer-provided)

1. **Official brochure PDF** — "Apartment Book Final" (35 pages), shared directly by the user. Provided floor plans (all unit types, all towers, all floors), master site plan, location map, exterior renders, amenity renders, and both rooftop landscape plans. Rendered into `assets/brochure_pages/`.
2. **Official Group Cost Sheet** — screenshot shared directly by the user, headed "Roach Cicada / Group Cost Sheet / Roach Lifescapes." Source of the full pricing breakdown and payment schedule in [03-pricing-and-payment-plan.md](03-pricing-and-payment-plan.md).
3. **Official WhatsApp sales broadcast** — text shared directly by the user, containing prelaunch offer pricing, precise location-advantage distance tables, and the outdoor/terrace/indoor amenity categorization used throughout this documentation.
4. [roachcicada.co](https://roachcicada.co/) — the current primary developer marketing website (Webflow-hosted). Source of project overview, unit configuration summary, and most exterior/amenity renders in `assets/web_images/`.
5. [cicada.roachlifescapes.com](https://cicada.roachlifescapes.com/) — developer's project subdomain under the main Roach Lifescapes site. Cross-checked specifications, location connectivity (minute-based distances), amenities list, and developer background; source of additional amenity icon images.
6. [roachcicada.in](https://roachcicada.in/) — an earlier/parallel developer-linked WordPress site ("RBD Roach Cicada"). Source of some site photos (`site-photo-*.jpg`) and an earlier pricing snapshot (flagged as stale in [08-rera-legal-and-fine-print.md](08-rera-legal-and-fine-print.md)).
7. [roachlifescapes.com](https://roachlifescapes.com/) — the developer's main corporate site, referenced via web search for company background, founding date, and other projects (RBD Stillwaters, RBD Meadows, Radisson Blu Hotel).

## Third-party (cross-verification only)

8. [Aurum PropTech — RERA Pulse](https://www.aurumproptech.in/pulse/rera/karnataka/bengaluru-urban/roach-cicada/14071) — RERA registration detail aggregator; source of the promoter legal name (RBD Shelters LLP), FAR, launch/completion dates, carpet+balcony area filed, litigation status, and tower-count discrepancy noted in [08-rera-legal-and-fine-print.md](08-rera-legal-and-fine-print.md).
9. [99acres.com listing](https://www.99acres.com/roach-cicada-junnasandra-bangalore-south-npxid-r457737) — third-party portal listing (referenced via search; direct fetch returned HTTP 403).
10. [NoBroker.in listing](https://www.nobroker.in/roach-cicada-sarjapur-road_bangalore-prjt-8aa99b219cdf7629019ce03a3c161aa7) — referenced via search results for cross-verification of project existence and basic facts.
11. [SquareYards listing](https://www.squareyards.com/bangalore-residential-property/roach-cicada/342209/project) — referenced via search results.
12. [QuikrHomes listing](https://www.quikr.com/homes/project/roach-cicada+sarjapur-road+bangalore+284063) — referenced via search results.
13. [PropertySuggest listing](https://propertysuggest.co/property/roach-cicada-junnasandra-sarjapur-road/) — referenced via search results.
14. [rbdroachcicada.com](https://rbdroachcicada.com/) — a further developer-linked domain surfaced via search ("700 Meters from WIPRO Corporate office"); not directly fetched, referenced only via search snippet.

## Notes on methodology

- Where sources disagreed (land area, unit sizes, tower count, historical pricing), the discrepancy is documented explicitly in [08-rera-legal-and-fine-print.md](08-rera-legal-and-fine-print.md) rather than silently resolved, so a RAG system can qualify its answers appropriately.
- All images in `assets/` were sourced from the developer's own official brochure and official websites. Per the user's confirmation, usage rights for these images have been granted by the developer.
- Web images were downloaded via direct HTTP fetch of URLs discovered in each site's HTML/CSS source. Brochure images were rendered from the source PDF at 150 DPI using `pdftoppm`.
