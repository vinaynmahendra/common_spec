---
id: "DOM-accessible-documents-and"
title: "Accessible documents and eBundles"
parent: "DOM-documents"
order: 3
type: "feature"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "Tagged PDF/UA for generated orders, awards and receipts; OCR layer and accessible-copy requests for uploaded documents; bookmarked eBundles"
links: []
rev: 2
syncHash: "17221f489722a666"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 6.5.3 Accessible documents and eBundles

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Tagged PDF/UA for generated orders, awards and receipts; OCR layer and accessible-copy requests for uploaded documents; bookmarked eBundles

<!-- section:scope -->
## Scope and surfaces

Covers documents the platform **generates** and the accessibility support it gives for documents users **upload**:

- Generated: procedural orders and awards produced from tenant templates, receipts and invoices ([[DOM-invoices-and-vendor-bills]]), proof-of-service certificates ([[DOM-service-of-notices-and-proof]]), transcripts ([[DOM-transcribers]]), eBundle index pages, separators and the bundle structure ([[DOM-ebundling]]), case summaries exported to PDF.
- Uploaded: pleadings, exhibits and other filings: OCR text layer, accessible-copy requests, and how bundles carry them.
- Media after the hearing: recordings and their captions or transcripts as accessible alternatives.

**Out of scope**: the document viewer UI ([[APP-document-viewer-and-sandbox]], [[PKG-document-viewer-controls]]); emails ([[PKG-notification-copy]]); the print theme itself ([[PKG-print-and-formal-document-theme]]), which this node relies on.

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

**Draft for legal sign-off.** The same instruments as the platform obligations register ([[APP-accessibility-legal-obligations]]) apply. Specific to documents:

| Instrument | Relevance | Who |
|---|---|---|
| RPwD Act 2016 [R1] and accessibility standards under it (IS 17802 / EN 301 549 chapter 10 for non-web documents) | Orders, awards and notices are services to parties | Tenant; Nomology by contract |
| SEBI digital accessibility circular (31 July 2025) [R2] | Documents issued to investors by regulated entities | Regulated tenant; flows down |
| Equal opportunity to present a case (Arbitration and Conciliation Act s.18 in India) | A party who cannot read the record is disadvantaged | Tribunal and institution |
| EN 301 549 chapter 10 [R3] | Non-web documents | Where applicable |

<!-- section:target -->
## Conformance target and baseline

- **Generated documents**: PDF/UA-1 (ISO 14289-1) conformant tagged PDF [R4], meeting WCAG 2.2 AA as applied to non-web documents by WCAG2ICT [R5].
- **eBundles**: tagged index and separators; bookmarks for every section and item; PDF page labels matching bundle page references; document language set; source documents carried with their existing tags; OCR text layer for scanned pages. Whole-bundle PDF/UA conformance cannot be guaranteed because sources are third-party; the bundle claims conformance only for generated parts.
- **Uploaded documents**: no conformance claim; the platform provides an OCR layer and an accessible-copy route.
- **Recordings**: certified transcript as the text alternative; captions file (WebVTT) when produced.
- Baseline: not yet measured.

<!-- section:criteria -->
## Success criteria mapping

| Requirement | Applies to | How met | Test |
|---|---|---|---|
| Tagged structure, reading order (WCAG 1.3.1, 1.3.2 via WCAG2ICT) | Generated docs | Templates render semantic HTML (headings, lists, tables with headers) to tagged PDF | PDF/UA validator in CI on fixture renders |
| Document title and language (2.4.2, 3.1.1, 3.1.2) | Generated docs, bundles | Title metadata set and displayed; `Lang` per document and per foreign-language passage | Validator + manual |
| Text alternatives (1.1.1) | Logos, seals, signatures in templates | Alt text required on every template image; decorative images artifacted | Template linter |
| Contrast (1.4.3) | Templates | Print theme tokens ([[PKG-print-and-formal-document-theme]]) | Contrast check |
| Bookmarks / navigation (2.4.5 multiple ways) | Bundles, long awards | Outline from headings; bundle outline per section and item | Programmatic check |
| Links (2.4.4) | Index, cross-references | Link text includes the destination label, e.g. "Exhibit C-12, page C/123" | Validator |
| Page labels | Bundles | `/PageLabels` equal to stamped references | Programmatic check |
| Tables (1.3.1) | Invoices, receipts, index | Header cells tagged `TH` with scope | Validator |
| Text of images (1.4.5) | Scanned uploads | OCR text layer; no conformance claim | OCR coverage metric |

<!-- section:at -->
## Assistive technology support matrix

| Reader setting | Browser / reader + AT | Depth |
|---|---|---|
| Counsel and neutrals, desktop | Adobe Acrobat Reader + NVDA and JAWS (Windows); Preview + VoiceOver (macOS) | Award, order, invoice, certificate and a bundle every release |
| Platform viewer | Chrome + NVDA, Safari + VoiceOver, using the text layer and bookmarks exposed by [[APP-document-viewer-and-sandbox]] | Same sample every release |
| Parties on mobile | iOS Files / Safari + VoiceOver; Android PDF viewer + TalkBack | Receipt and certificate every release |
| Low vision | Acrobat reflow and high-contrast; viewer zoom 400% | Award and bundle index each major release |

<!-- section:documents -->
## Documents, media and generated output

**Generation pipeline**: tenant templates are HTML with the print theme, rendered to tagged PDF by a renderer that outputs structure tags (candidate: headless Chromium's tagged PDF output, to be verified against PDF/UA validation), then post-processed to set metadata and validated. A template that fails validation cannot be published by the tenant.

**Uploaded documents**: OCR runs in [[WF-long-running-pipelines]] for image-only PDFs and images, adding an invisible text layer to a rendition (the original is unchanged). A party or neutral can request an accessible copy of any document: the request goes to the filer (and secretariat), who can upload an accessible version linked as `accessible_copy_of`; the secretariat can produce one if the filer does not.

**AI**: AI-generated alt text or summaries are never inserted into a filed document; they may be offered as labelled aids in the viewer after human review ([[AI-ai-generated-text-labelling-and]]).

<!-- section:tenant -->
## Tenant theming and configuration guardrails

Tenant-uploaded templates (award, order, receipt) are validated at save: required title, language, alt text on images, heading structure, table headers, contrast of template colours; failures block publication with a list of fixes. Tenants cannot upload pre-built PDFs as templates. Custom fonts must include the glyphs for the template's languages and embed Unicode mappings so text is extractable.

<!-- section:testing -->
## Testing method

- CI renders every platform template and a sample of each tenant template with fixture data in English, Hindi and Chinese, and runs a PDF/UA validator; failures block release.
- Bundle golden tests check bookmarks, page labels, link targets and tagged index.
- Manual checks each release with NVDA + Adobe Acrobat Reader, VoiceOver + Preview on macOS, and the platform viewer, on one award, one invoice, one certificate and one bundle.
- OCR quality sampled monthly per language (character accuracy on a labelled set).

<!-- section:exceptions -->
## Known exceptions and remediation plan

| Gap | Impact | Workaround | Owner |
|---|---|---|---|
| Uploaded third-party documents are often untagged | Screen-reader users get OCR text without structure | Accessible-copy request with deadline consideration | Product |
| OCR quality for some Indian scripts | Poor text layer | Human accessible copy on request | Documents team |
| Whole-bundle PDF/UA not achievable with untagged sources | Bundle partially conformant | Claim limited to generated parts, stated in the ACR | Accessibility lead |

<!-- section:reporting -->
## Conformance reporting

Generated-document conformance is reported in the platform ACR (VPAT INT edition, WCAG2ICT and EN 301 549 chapter 10 rows) via [[APP-accessibility-conformance]], with the bundle limitation stated. Tenant accessibility statements list how to request accessible copies.

<!-- section:support -->
## Feedback, accommodation and grievance

Accessible-copy requests are raised from the document's menu, routed to the filer and the tribunal secretary as a human task (proposed response target 5 business days, 2 if a hearing is within 7 days). The tribunal can extend a deadline that depends on the document; the request is shown on the case timeline as a procedural request.

<!-- section:questions -->
## Open questions

- [ ] Choose and verify the tagged-PDF renderer and validator in CI (licence and accuracy for Indic and CJK scripts).
- [ ] Should the accessible-copy request automatically pause or extend related deadlines, or always need a tribunal decision? Legal / product.
- [ ] Do tenants need DOCX or HTML versions of awards as accessible alternatives in addition to PDF?

<!-- checks -->
## Template checks

<!-- check:applicability -->
### Legal applicability and allocation

Obligations per tenant type follow the platform register, with documents-specific rows above (draft for legal). The MSA states PDF/UA for generated documents and the limitation for uploaded content and bundles.

<!-- check:evidence -->
### Integrity of the conformance claim

Each release stores validator reports for every platform template and the golden bundle, with build hash, as ACR evidence. The bundle claim is scoped to generated parts; the third-party content limitation is stated narrowly, together with the accessible-copy route.

<!-- check:tenancy -->
### Tenant customisation and content

Tenant templates are validated at save and cannot be published if they fail; tenant fonts must embed Unicode mappings. Each tenant's accessibility statement includes its own accessible-copy contact.

<!-- check:regression -->
### Preventing regression

Template rendering plus PDF/UA validation runs in CI on every change to templates, the renderer or the print theme; bundle golden tests run on every change to the bundling pipeline.

<!-- check:due-process -->
### Equal participation in proceedings

Accessible-copy requests are procedural requests with response targets; the tribunal can extend dependent deadlines; recordings get certified transcripts as alternatives within the same turnaround as for other users.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Requires accessibility of services and information under standards made under the Act.",
    "id": "R1",
    "issuer": "Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 49 of 2016",
    "title": "Rights of Persons with Disabilities Act, 2016",
    "url": "https://indiacode.nic.in/bitstream/123456789/15939/1/the_rights_of_persons_with_disabilities_act%2C_2016.pdf"
  },
  {
    "excerpt": "Digital accessibility compliance guidelines for SEBI-regulated entities.",
    "id": "R2",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "SEBI circular, 31 July 2025",
    "title": "Compliance guidelines for digital accessibility (circular dated 31 July 2025)",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  },
  {
    "body": "ETSI",
    "clause": "Chapter 10",
    "excerpt": "Chapter 10 sets accessibility requirements for non-web documents.",
    "id": "R3",
    "ident": "EN 301 549",
    "kind": "standard",
    "title": "ETSI EN 301 549 V3.2.1 Accessibility requirements for ICT products and services",
    "url": "https://www.etsi.org/deliver/etsi_en/301500_301599/301549/03.02.01_60/en_301549v030201p.pdf",
    "version": "V3.2.1 (2021-03)"
  },
  {
    "body": "ISO (resource page by PDF Association)",
    "excerpt": "ISO 14289 (PDF/UA) specifies requirements for accessible PDF documents.",
    "id": "R4",
    "ident": "ISO 14289 (PDF/UA)",
    "kind": "standard",
    "title": "ISO 14289 (PDF/UA)",
    "url": "https://pdfa.org/resource/iso-14289-pdfua/"
  },
  {
    "body": "W3C",
    "excerpt": "Guidance on applying WCAG 2.2 success criteria to non-web documents and software.",
    "id": "R5",
    "ident": "WCAG2ICT",
    "kind": "standard",
    "title": "Applying WCAG 2.2 to Non-Web Information and Communications Technologies (WCAG2ICT)",
    "url": "https://www.w3.org/TR/wcag2ict-22/"
  }
]
```

<!-- end -->
