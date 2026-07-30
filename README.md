# agent-core run-engine example

Mini app showing the current agent-core architecture: a persisted autonomous
run, an LLM provider, a scoped tool registry, a policy engine, exact provider
token usage, and an optional Pydantic JSON output contract.

PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
$env:OPENAI_API_KEY = "..."
poem-agent "Write a short poem about patience"
poem-agent --json "Write a haiku about an old terminal"
poem-agent --show-usage "Write four lines about a lighthouse"
```

Bash:

```bash
git clone https://github.com/maxDcb/agent-core-exemple.git
cd agent-core-exemple
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export OPENAI_API_KEY="..."
poem-agent "Write a short poem about patience"
poem-agent --json "Write a haiku about an old terminal"
poem-agent --show-usage "Write four lines about a lighthouse"
```

The agent can only read files inside `workspace/`. It is instructed to read
`workspace/theme.txt`, then write a poem from the user input and that file
theme. Each invocation creates a durable run under `sessions/agent-runs/`.

`--show-usage` prints the run-level usage summary after the poem. Exact totals
are present when every provider response reports usage; otherwise totals remain
unavailable rather than being replaced with character-based estimates.

The example imports the run engine from `agent_core` and extension contracts
from `agent_core.spi`. For development against a local checkout:

```powershell
pip install -e E:\Dev\agent-core
pip install -e ".[dev]" --no-deps
pip install "pydantic>=2,<3" "pytest>=7" "ruff>=0.5"
pytest
```

On Bash, replace the three installation commands above with:

```bash
pip install -e ../agent-core
pip install -e ".[dev]" --no-deps
pip install "pydantic>=2,<3" "pytest>=7" "ruff>=0.5"
pytest
```
