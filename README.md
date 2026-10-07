# LangGraph Coder Agent

An autonomous coding agent built with Python and LangGraph. It turns a high-level programming task into a structured execution plan, creates the required files, writes implementation code, runs the program, and loops back to fix failures until the solution is satisfactory or the retry limit is reached.

This project is designed to behave a bit like a minimal software-development loop:

- Understand the request
- Plan the work
- Create files
- Generate code
- Run the code
- Inspect failures
- Repair the implementation
- Repeat until the task is complete

---

## What this agent does

The agent reads a task description from `fix.txt`, sends it into a LangGraph state machine, and then coordinates a few specialized steps:

1. Planner decides what the solution should look like
2. File manager creates the necessary file(s)
3. Coder writes the implementation
4. Tester executes the code
5. If the code fails, the tester asks the model for a fix
6. The system loops until the task is solved or gives up

This is a very lightweight autonomous coding workflow rather than a full production IDE. It is best understood as a directed graph of agent states, each one responsible for a single phase of the software-building loop.

---

## Repository layout

```text
.
├── agent.py              # Main LangGraph agent and execution loop
├── tools.py              # Placeholder / extension point for additional tools
├── webpage/              # Static HTML/CSS/JS portfolio/demo frontend
├── .gitignore            # Git ignore file
└── fix.txt               # Runtime input file for the task prompt (created by the user at runtime)
```

Notes:

- `agent.py` is the core of the project.
- `webpage/` contains a separate front-end demo unrelated to the agent logic itself.
- `fix.txt` is expected to exist when the agent is run; it is the task input file.

---

## Core idea: the LangGraph workflow

The system is implemented as a `StateGraph` in `agent.py`.

### States

- `planner`
  - Converts the user's request into a JSON plan.
  - Produces a list like:
    - `file: app.py`
    - `code: create the implementation`
    - `test: app.py`
    - `exit`
  - Stores the plan in `plan.txt`.

- `router`
  - Reads the current instruction from the plan.
  - Routes the workflow to the next node based on the instruction type.
  - Recognizes steps beginning with `file`, `code`, `test`, or `exit`.

- `file`
  - Creates the target file on disk before coding begins.

- `coder`
  - Writes the actual code for the current file.
  - Uses the current plan and prior code context to generate implementation.
  - Saves code directly to the file path.

- `tester`
  - Runs the file using a command derived from its extension.
  - Detects runtime errors or logic errors.
  - If the result is wrong, it asks the LLM to explain what failed.

- `exit`
  - Ends the workflow.

### Example flow

```text
START -> planner -> router -> file -> coder -> tester -> router -> coder -> tester -> ... -> exit -> END
```

The loop continues until the code passes the checks or the agent decides it cannot make progress.

---

## How the planner works

The `planner` function constructs a system prompt for the LLM and asks it to output a valid JSON plan.

It tells the model:

- to pick the programming language
- to break the problem into a small set of steps
- to create files with explicit paths
- to keep the plan concise
- to include a `test` step when code should be validated

The result is saved into `plan.txt` and also stored in the graph state as:

- `plan`
- `language`
- `instr`
- `file_path`

The agent keeps track of which step it is on through the `instr` index.

---

## How the coder works

The `coder` function is responsible for generating implementation code.

It:

- reads the current plan step
- reads any existing file content if the file already exists
- includes the plan and current code context in the prompt
- asks the LLM to output a JSON object with:
  - `code`
  - `test_case`
  - `output`
- writes the returned code to the file path

This is intentionally simple but effective: the model generates an implementation directly from the task and the current project state.

---

## How testing works

The `tester` node handles validation.

### Automatic execution

For a given file path, the agent chooses a command based on the extension:

| Extension | Command used |
| --- | --- |
| `.py` | `python3 file.py` |
| `.c` | `gcc file.c -o temp && ./temp` |
| `.cpp` | `g++ file.cpp -o temp && ./temp` |
| `.js` | `node file.js` |
| `.ts` | `npx ts-node file.ts` |
| `.sh` | `bash file.sh` |
| `.java` | `javac file.java && java ClassName` |
| `.rs` | `rustc file.rs -o temp && ./temp` |
| `.go` | `go run file.go` |

### Failure handling

If the code fails:

- the output is captured
- the LLM is asked to diagnose the issue
- it returns a structured `TestOut` object containing:
  - a human-readable error comment
  - whether a terminal command can solve the issue
  - the exact command to run

If the fix is possible via terminal setup or package installation, the test node may attempt it. Otherwise, it sends feedback back to the coder for another implementation pass.

---

## Self-correcting loop

One of the most important parts of the project is its retry mechanism.

The workflow behaves like this:

- generate code
- run it
- if it fails, produce error feedback
- send that feedback back into `coder`
- regenerate the solution
- repeat

The state includes fields like:

- `comments`
- `test_count`
- `ran_successfully`
- `output_case`

This allows the agent to remember what failed and avoid endlessly re-running the same broken logic.

---

## Required environment and setup

This project expects a model API key in the environment.

### 1. Install dependencies

```bash
pip install python-dotenv langchain-openai langgraph langchain langchain-core pydantic
```

### 2. Create a `.env` file

```bash
HARBOUR_API_KEY=your_api_key_here
```

The code currently points to a remote model hosted on TokenHarbor:

```python
llm = ChatOpenAI(
    model="glm-5.3-flash",
    api_key=os.environ.get("HARBOUR_API_KEY"),
    base_url="https://tokenharbor.ai/v1",
    temperature=0
)
```

If you prefer a different model vendor, you can swap in a different `ChatOpenAI` configuration in `agent.py`.

---

## How to run it

1. Create a task file called `fix.txt` in the project root.
2. Put your assignment or bug description inside it.
3. Run:

```bash
python agent.py
```

Example `fix.txt` content:

```text
Build a Python script that reads a number from the user and prints whether it is even or odd.
```

The agent will then:

- plan the work
- create the file
- generate the code
- test the result
- fix issues if needed

---

## What happens at runtime

When the script runs, it does the following:

1. Loads environment variables from `.env`
2. Builds the LangGraph state machine
3. Reads the prompt from `fix.txt`
4. Streams the conversation through the graph
5. Generates a `plan.txt` file
6. Creates target files
7. Writes code and runs it
8. Loops until completion or failure threshold

The terminal output is streamed live so you can see each phase of the agent work in progress.

---

## Important implementation notes

- The project uses a memory checkpoint system from `langgraph.checkpoint.memory.InMemorySaver`.
- The graph is state-based, so each step passes structured data between nodes.
- The logic is intentionally compact and educational rather than highly productionized.
- The agent is simple but effective for small code generation and debugging tasks.
- It is not a general-purpose IDE or full repository-aware software engineer.

---

## Limitations

This is a solid prototype, but it has some practical limitations:

- It assumes a single task input file (`fix.txt`) and works best for focused coding tasks.
- It does not deeply inspect a large project tree.
- The test loop is basic and targeted at small scripts and command-line programs.
- The output depends strongly on the quality of the underlying LLM model.
- It is not automatically integrated with Git or a developer environment.

---

## Example use cases

This repo is useful for:

- generating small scripts from prompts
- solving algorithmic coding tasks
- debugging simple runtime issues
- creating quick prototypes in Python, C, JavaScript, or other supported languages

---

## About the webpage folder

The `webpage/` directory is a separate static website template included in the repo. It is not the agent itself, but it shows the repository also contains a front-end demo or portfolio example.

It uses:

- HTML
- CSS
- JavaScript
- Font Awesome
- Google Fonts

This folder is not required for the agent brain to function.

---

## Summary

`langgraph-coder-agent` is a compact experimental autonomous coding system that combines:

- LLM planning
- LangGraph state-based orchestration
- file generation
- runtime testing
- self-correction loops

It is a practical example of using LangGraph to build a simple agent that writes and repairs code iteratively.

If you want, the next step could be to add:

- a proper CLI interface
- support for multi-file projects
- better repo-aware planning
- Git-based versioning
- a richer web dashboard

---

## License

No license file is currently included in this repository, so the default legal status is repository-default unless you explicitly add one.

If this project is intended for public or commercial use, consider adding an open-source license such as MIT or Apache 2.0.
