## Fertilizer Recommendation — LLM Strategy

### Objective
Obtain reliable, structured N/P/K fertilizer recommendations per crop (g/m2), including basal/topdress split and counts, with minimal, reproducible prompting.

### Unit & Nutrient Convention
- All quantities are elemental nutrients in g/m2: `N`, `P`, `K`.
- If sources report oxide forms, convert: `P = P2O5 × 0.4364`, `K = K2O × 0.8301`.

### Retrieval
- Query terms: `<crop common name> fertilizer requirement NPK site:*.go.jp OR site:extension.* OR site:*.agriculture.*` (prefer government/extension)
- Provide 2–5 brief context snippets (title + 1–2 sentences) to the model.

### Determinism & Safety
- Temperature: 0–0.2; top_p: 0.9; max tokens: sized for response schema
- Seed where supported
- Retry only on schema/validation errors (max 2 retries)
- No silent fallbacks; return explicit error on repeated schema violations

### Output Schema (UseCase DTO excerpt)
```
{
  "crop": { "crop_id": string, "name": string },
  "totals": { "N": number, "P": number, "K": number },
  "applications": [
    {
      "type": "basal" | "topdress",
      "count": number,
      "schedule_hint": string | null,
      "nutrients": { "N": number, "P": number, "K": number },
      "per_application": { "N": number, "P": number, "K": number } | null
    }
  ],
  "sources": string[],
  "confidence": number,
  "notes": string | null
}
```

### System Prompt (template)
```
You are an agronomy assistant. Return fertilizer recommendations strictly as JSON.
Rules:
- Units: elemental N, P, K in g/m2.
- If inputs use P2O5/K2O, convert using P=P2O5*0.4364 and K=K2O*0.8301.
- Totals must equal the sum of applications per nutrient (±1e-6).
- Include at least one application. Prefer a basal and (if relevant) 1–2 topdress splits.
- Provide 2–5 concise sources as strings (URL or citation text).
- Do not include text outside JSON.
```

### User Prompt (example)
```
Crop: {name: "Tomato", variety: ""}
Region: JP-Temperate (if known)
Goal: Provide N/P/K totals (g/m2) and a basal/topdress plan appropriate for field production. 
Context:
1) {title}: {snippet}
2) {title}: {snippet}
...
Return JSON matching the schema. If ranges are given, choose a single reasonable point and note the assumption in notes.
```

### Validation & Post-processing
- JSON schema validation (shape and numeric types)
- Invariant checks: totals ≥ 0; application sums equal totals
- Optional normalization: round to 0.1 g/m2 precision

### Error Handling
- On schema error: respond with validator error messages, ask the model to correct. Up to 2 retries.
- On repeated failure: surface a gateway error to interactor.

### Notes
- Keep prompts short; front-load unit constraints and conversions.
- Prefer authoritative sources; if conflicting, pick conservative values and note in `notes`.

