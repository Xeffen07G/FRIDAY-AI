# F.R.I.D.A.Y. Orchestration Lifecycle

## Intent Classification
To minimize latency, F.R.I.D.A.Y. uses a lightweight regex-based intent detector before invoking the LLM:
- **`conversational`**: Greetings and small talk (bypasses tools).
- **`memory_save`**: Declarative facts (triggers confirmation mode).
- **`tool_execution`**: Explicit requests for math, files, or system info.
- **`routing_needed`**: Complex queries requiring LLM-based tool selection.

## Hard-Caps and Fallbacks
- **Orchestration Timeout**: The tool routing phase is strictly capped at 2.0 seconds. If the LLM doesn't respond in time, the system falls back to a direct conversational response.
- **Async Execution**: Tool execution and memory storage happen in non-blocking threads to keep the token stream fluid.

## Dynamic Profiles
Generation parameters are adjusted based on intent:
- **`FAST_CHAT`**: Low temperature, low `num_predict` for snappy greetings.
- **`MEMORY_CHAT`**: Balanced for factual accuracy.
- **`TOOL_MODE`**: Optimized for following structured data instructions.
