# Roach Cicada — Property Knowledge Base

Research and documentation package for **Roach Cicada**, a residential apartment project by **Roach Lifescapes LLP** (formerly RBD Shelters LLP) in Junnasandra, off Sarjapur Road, East Bangalore.

**Purpose:** This folder is source material for a RAG (retrieval-augmented generation) system that answers buyer questions about this property. Content is organized into small, topic-focused Markdown files so each chunks cleanly for embedding/retrieval. Every file favors concrete numbers over marketing language, and notes data provenance so the model can qualify uncertain figures.

## Quick facts (canonical snapshot)

| Field | Value |
|---|---|
| Project name | Roach Cicada |
| Developer | Roach Lifescapes LLP (formerly RBD Shelters LLP) |
| Location | Junnasandra Main Road, off Sarjapur Road, Varthur Hobli, Bengaluru East, Karnataka 560035 — opposite the old Wipro campus |
| Land parcel | 2.65 acres (developer marketing figure; RERA filing records ~3.14–3.15 acres — see [08-rera-legal-and-fine-print.md](08-rera-legal-and-fine-print.md)) |
| Configuration | 3 towers (A, B, C), B+G+10 floors, 2-level basement parking |
| Total units | 124 boutique apartments |
| Unit types | 3 BHK, 3.5 BHK, 4.5 BHK (some listings also show a 2.5 BHK variant) |
| Sizes (super built-up) | 2,105 – 2,954 sq.ft. depending on type and floor |
| Prelaunch base rate | ₹13,200 per sq.ft (basic rate, before GST/charges) |
| Indicative all-in price | ₹3.18 Cr (3 BHK) to ₹4.29 Cr (4.5 BHK), grand total incl. GST & charges |
| RERA registration | PRM/KA/RERA/1251/446/PR/051225/008318 |
| Approvals | BBMP approved, RERA approved |
| Possession (marketed) | December 2029 |
| RERA completion date (filed) | 5 August 2030 |
| Amenities | 50+ across outdoor, terrace, and indoor categories |
| Booking status | Bookings open (prelaunch offer live as of Aug 2026) |
| Sales contact | +91 81472 29590 |

## File index

| File | Covers |
|---|---|
| [01-project-overview.md](01-project-overview.md) | What the project is, structure, land, positioning, design philosophy |
| [02-unit-types-and-floor-plans.md](02-unit-types-and-floor-plans.md) | Every unit type, room-by-room dimensions, SBA vs RERA carpet area, per-floor variants |
| [03-pricing-and-payment-plan.md](03-pricing-and-payment-plan.md) | Official cost sheet, per-unit-type price breakdown, construction-linked payment schedule, fine print |
| [04-location-and-connectivity.md](04-location-and-connectivity.md) | Address, distances to IT parks, hospitals, schools, retail, metro, roads |
| [05-amenities.md](05-amenities.md) | Full amenity list by outdoor/terrace/indoor category |
| [06-master-plan-and-landscape.md](06-master-plan-and-landscape.md) | Site layout, master plan legend, landscape/terrace plan legends |
| [07-developer-profile.md](07-developer-profile.md) | Roach Lifescapes / RBD Shelters background, track record, other projects |
| [08-rera-legal-and-fine-print.md](08-rera-legal-and-fine-print.md) | RERA registration details, promoter/legal entity, data discrepancies across sources, cost-sheet fine print |
| [09-faq.md](09-faq.md) | Direct buyer Q&A — the highest-value file for RAG retrieval |
| [10-sources.md](10-sources.md) | Every source used, with URLs, and what each contributed |
| [11-sample-flat-and-media.md](11-sample-flat-and-media.md) | Real sample-flat photography, additional exterior renders, and videos |

## Assets

- `assets/brochure_pages/` — all 35 pages of the official developer brochure ("Apartment Book Final"), rendered as numbered, descriptively-named PNG images (floor plans, master plan, location map, amenity renders, landscape plans).
- `assets/web_images/` — exterior renders, amenity photos, and the project logo, downloaded from the developer's own websites (roachcicada.co, roachcicada.in, cicada.roachlifescapes.com).
- `assets/exterior-renders-v2/` — 16 additional exterior/site CGI renders.
- `assets/sample-flat-photos/` — 55 real photographs of a furnished show flat (bedrooms, kitchen, bathroom, living/dining).
- `assets/videos/` — an official marketing fly-through video and real sample-flat walkthrough footage.
- `assets/unrelated-do-not-use/` — one video that was mixed into the source material but is unrelated to this project; excluded from documentation and retrieval.

Image filenames are descriptive (e.g. `11-floorplan-3bhk-towerAC-3rd6th9th-sba2161-rera1354.png`) so they can be cited or retrieved by topic without opening them first.

## Chatbot demo

`chatbot/` contains a local RAG-powered chat demo — a real-estate-sales-persona assistant (built for HNI/NRI buyers) that answers questions grounded in this knowledge base and surfaces relevant photos/videos inline. See [chatbot/README.md](chatbot/README.md) to run it.
