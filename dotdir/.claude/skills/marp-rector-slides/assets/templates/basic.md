---
marp: true
theme: default
paginate: true
---

<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {
  theme: {
    extend: {
      colors: {
        navy: '#1B4565',
        teal: '#3E9BA4',
        'bg-secondary': '#F5F5F5',
        'text-secondary': '#4A4A4A',
        'text-muted': '#6B6B6B',
      },
      fontSize: {
        'em-3xl': ['3em', { lineHeight: '1.1' }],
        'em-2xl': ['2em', { lineHeight: '1.2' }],
        'em-xl': ['1.5em', { lineHeight: '1.3' }],
        'em-lg': ['1.25em', { lineHeight: '1.5' }],
        'em-base': ['1em', { lineHeight: '1.6' }],
      }
    }
  }
}
</script>

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
    <span class="text-em-2xl text-teal block mb-4">🚀</span>
    <h3 class="text-em-lg text-navy mb-4">Feature One</h3>
    <p class="text-em-base text-text-secondary">Brief description</p>
  </div>
  <div class="bg-bg-secondary rounded-lg p-6 text-center">
    <span class="text-em-2xl text-teal block mb-4">⚡</span>
    <h3 class="text-em-lg text-navy mb-4">Feature Two</h3>
    <p class="text-em-base text-text-secondary">Brief description</p>
  </div>
  <div class="bg-bg-secondary rounded-lg p-6 text-center">
    <span class="text-em-2xl text-teal block mb-4">🎯</span>
    <h3 class="text-em-lg text-navy mb-4">Feature Three</h3>
    <p class="text-em-base text-text-secondary">Brief description</p>
  </div>
</div>

---

<!-- Big Number / Statistic -->

<div class="flex flex-col items-center justify-center h-full text-center">
  <span class="text-em-3xl text-teal font-bold">85%</span>
  <p class="text-em-xl text-navy mt-4">Improvement in efficiency</p>
  <p class="text-em-base text-text-muted mt-4">Based on customer feedback</p>
</div>

---

<!-- Quote -->

<div class="flex items-center justify-center h-full">
  <blockquote class="max-w-2xl text-center">
    <p class="text-em-xl text-navy italic mb-6">
      "A memorable quote that resonates with your audience and reinforces your message."
    </p>
    <cite class="text-em-base text-text-muted">— Author Name, Title</cite>
  </blockquote>
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
