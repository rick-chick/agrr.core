## Fertilizer Recommendation — Testing Strategy

### Principles
- テストファースト。各層の単体テストを用意
- パッチは禁止。依存はDIで注入し、conftestにモックを定義
- integrationテストはadapter層を直接テスト

### Unit (UseCase)
- Target: `fertilizer_llm_recommend_interactor`
- Inject fake `fertilizer_llm_recommend_gateway`
- Cases:
  - valid tomato request → totals and applications sum; citations present
  - invalid negative values from gateway → interactor rejects
  - gateway schema violation → interactor triggers controlled failure

### Adapter Integration (later)
- Memory adapter: deterministic fixed responses
- LLM adapter: skipped by default; enable via marker and requires API key

### Fixtures
- `tests/conftest.py`: fake gateway implementations and sample payloads

### Validation Helpers
- JSON schema for response shape (UseCase-level)
- Sum check helper to ensure applications equal totals


