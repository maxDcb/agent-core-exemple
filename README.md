# agent-core poem example

Mini app showing the basic agent-core pieces: an LLM provider, a tool registry, a policy engine, and an optional Pydantic JSON output contract.

PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
$env:OPENAI_API_KEY = "..."
poem-agent "Write a short poem about patience"
poem-agent --json "Write a haiku about an old terminal"
```

Bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export OPENAI_API_KEY="..."
poem-agent "Write a short poem about patience"
poem-agent --json "Write a haiku about an old terminal"
```

The agent can only read files inside `workspace/`. It is instructed to read `workspace/theme.txt`, then write a poem from the user input and that file theme.
