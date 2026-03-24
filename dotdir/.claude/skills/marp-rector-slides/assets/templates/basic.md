---
marp: true
theme: default
paginate: true
style: |
  /* === Colors === */
  .text-navy { color: #1B4565; }
  .text-teal { color: #3E9BA4; }
  .text-text-secondary { color: #4A4A4A; }
  .text-text-muted { color: #6B6B6B; }
  .text-red { color: #E53E3E; }
  .text-green { color: #38A169; }
  .text-amber { color: #D69E2E; }
  .text-white { color: #fff; }
  .bg-bg-secondary { background-color: #F5F5F5; }
  .bg-teal { background-color: #3E9BA4; }
  .bg-navy { background-color: #1B4565; }
  .bg-red.bg-opacity-5 { background-color: rgba(229,62,62,0.05); }
  .bg-amber.bg-opacity-5 { background-color: rgba(214,158,46,0.05); }
  .bg-teal.bg-opacity-10 { background-color: rgba(62,155,164,0.1); }
  .bg-teal.bg-opacity-20 { background-color: rgba(62,155,164,0.2); }
  /* === Typography === */
  .text-em-3xl { font-size: 3em; line-height: 1.1; }
  .text-em-2xl { font-size: 2em; line-height: 1.2; }
  .text-em-xl { font-size: 1.5em; line-height: 1.3; }
  .text-em-lg { font-size: 1.25em; line-height: 1.5; }
  .text-em-base { font-size: 1em; line-height: 1.6; }
  .text-em-sm { font-size: 0.85em; line-height: 1.4; }
  .font-bold { font-weight: 700; }
  .text-center { text-align: center; }
  .text-left { text-align: left; }
  .leading-relaxed { line-height: 1.625; }
  /* === Layout: Flex === */
  .flex { display: flex; }
  .flex-col { flex-direction: column; }
  .items-center { align-items: center; }
  .items-start { align-items: flex-start; }
  .justify-center { justify-content: center; }
  .justify-between { justify-content: space-between; }
  /* === Layout: Grid === */
  .grid { display: grid; }
  .grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
  .grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
  .col-span-2 { grid-column: span 2 / span 2; }
  .gap-2 { gap: 0.5rem; } .gap-3 { gap: 0.75rem; }
  .gap-4 { gap: 1rem; } .gap-6 { gap: 1.5rem; } .gap-8 { gap: 2rem; }
  /* === Sizing === */
  .w-full { width: 100%; } .h-full { height: 100%; }
  .block { display: block; }
  /* === Spacing === */
  .p-2 { padding: 0.5rem; } .p-3 { padding: 0.75rem; }
  .p-4 { padding: 1rem; } .p-6 { padding: 1.5rem; } .p-8 { padding: 2rem; }
  .pl-8 { padding-left: 2rem; }
  .py-0 { padding-top: 0; padding-bottom: 0; }
  .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
  .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
  .mb-0 { margin-bottom: 0; } .mb-1 { margin-bottom: 0.25rem; }
  .mb-2 { margin-bottom: 0.5rem; } .mb-4 { margin-bottom: 1rem; }
  .mb-6 { margin-bottom: 1.5rem; } .mb-8 { margin-bottom: 2rem; }
  .mt-0 { margin-top: 0; } .mt-2 { margin-top: 0.5rem; }
  .mt-4 { margin-top: 1rem; } .mt-8 { margin-top: 2rem; }
  .mr-2 { margin-right: 0.5rem; } .mr-3 { margin-right: 0.75rem; }
  .mr-4 { margin-right: 1rem; }
  .space-y-2 > * + * { margin-top: 0.5rem; }
  .space-y-3 > * + * { margin-top: 0.75rem; }
  .space-y-4 > * + * { margin-top: 1rem; }
  /* === Border === */
  .border-l-4 { border-left: 4px solid; }
  .border-b { border-bottom: 1px solid #e5e7eb; }
  .border-b-2 { border-bottom: 2px solid; }
  .border-2 { border-width: 2px; border-style: solid; }
  .border-navy { border-color: #1B4565; }
  .border-teal { border-color: #3E9BA4; }
  .rounded { border-radius: 0.25rem; }
  .rounded-lg { border-radius: 0.5rem; }
  .rounded-full { border-radius: 9999px; }
  /* === Table fix: Marp sets display:block on all table elements === */
  section table { display: table !important; width: 100% !important; table-layout: auto; border-collapse: collapse; }
  section table thead { display: table-header-group !important; }
  section table tbody { display: table-row-group !important; }
  section table tr { display: table-row !important; }
  section table th, section table td { display: table-cell !important; }
---

<!-- _class: title -->

<div class="flex flex-col items-center justify-center h-full text-center">
  <h1 class="text-em-3xl text-navy mb-4">Presentation Title</h1>
  <p class="text-em-xl text-text-secondary">Subtitle or tagline goes here</p>
</div>

---

<!-- Section Break -->

<div class="flex items-center h-full">
  <div class="border-l-4 border-teal pl-8">
    <p class="text-em-base text-text-muted mb-4">Section 01</p>
    <h2 class="text-em-2xl text-navy">Section Title</h2>
  </div>
</div>

---

<!-- Two Column Layout -->

<div class="grid grid-cols-2 gap-8 h-full items-center">
  <div>
    <h2 class="text-em-2xl text-navy mb-4">Left Column</h2>
    <p class="text-em-lg text-text-secondary">
      Content for the left side. Keep it focused and concise.
    </p>
  </div>
  <div class="bg-bg-secondary rounded-lg p-6">
    <p class="text-em-lg text-text-secondary">
      Right column content or image placeholder.
    </p>
  </div>
</div>

---

<!-- Bullet Points -->

<h2 class="text-em-2xl text-navy mb-8">Key Points</h2>

<div class="space-y-4">
  <div class="flex items-start">
    <span class="text-teal mr-4">●</span>
    <span class="text-em-lg">First important point with explanation</span>
  </div>
  <div class="flex items-start">
    <span class="text-teal mr-4">●</span>
    <span class="text-em-lg">Second point that builds on the first</span>
  </div>
  <div class="flex items-start">
    <span class="text-teal mr-4">●</span>
    <span class="text-em-lg">Third point that concludes the section</span>
  </div>
</div>

---

<!-- Three Column Features -->

<h2 class="text-em-2xl text-navy mb-8 text-center">Features</h2>

<div class="grid grid-cols-3 gap-6">
  <div class="bg-bg-secondary rounded-lg p-6 text-center">
    <h3 class="text-em-lg text-navy mb-4">Feature One</h3>
    <p class="text-em-base text-text-secondary">Brief description</p>
  </div>
  <div class="bg-bg-secondary rounded-lg p-6 text-center">
    <h3 class="text-em-lg text-navy mb-4">Feature Two</h3>
    <p class="text-em-base text-text-secondary">Brief description</p>
  </div>
  <div class="bg-bg-secondary rounded-lg p-6 text-center">
    <h3 class="text-em-lg text-navy mb-4">Feature Three</h3>
    <p class="text-em-base text-text-secondary">Brief description</p>
  </div>
</div>

---

<!-- Table Example -->

<h2 class="text-em-xl text-navy mb-4">Data Table</h2>

<table class="w-full text-em-sm">
  <thead>
    <tr class="border-b-2 border-navy">
      <th class="text-left py-2 text-navy">Column A</th>
      <th class="text-center py-2 text-navy">Column B</th>
      <th class="text-center py-2 text-navy">Column C</th>
    </tr>
  </thead>
  <tbody class="text-text-secondary">
    <tr class="border-b"><td class="py-1">Row 1</td><td class="text-center">Value</td><td class="text-center">Value</td></tr>
    <tr class="border-b"><td class="py-1">Row 2</td><td class="text-center">Value</td><td class="text-center">Value</td></tr>
    <tr><td class="py-1">Row 3</td><td class="text-center">Value</td><td class="text-center">Value</td></tr>
  </tbody>
</table>

---

<!-- Big Number / Statistic -->

<div class="flex flex-col items-center justify-center h-full text-center">
  <span class="text-em-3xl text-teal font-bold">85%</span>
  <p class="text-em-xl text-navy mt-4">Improvement in efficiency</p>
  <p class="text-em-base text-text-muted mt-4">Based on customer feedback</p>
</div>

---

<!-- Thank You / Closing -->

<div class="flex flex-col items-center justify-center h-full text-center">
  <h2 class="text-em-3xl text-navy mb-6">Thank You</h2>
  <p class="text-em-lg text-text-secondary mb-8">Questions?</p>
  <div class="text-em-base text-text-muted">
    <p>email@example.com</p>
    <p>@twitter_handle</p>
  </div>
</div>
