# LangGraph Coder Agent 🤖

An autonomous coding agent built with **Python** and **LangGraph** that automatically solves complex programming assignments. The agent translates programming tasks into structured execution plans, dynamically generates project files, writes production-ready code, and autonomously debugs and refines its output through a self-correcting testing loop.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [How the Agent Works](#how-the-agent-works)
- [Workflow Diagram](#workflow-diagram)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Agent States & Components](#agent-states--components)
- [Workflow Steps](#workflow-steps)

---

## Features

✨ **Key Capabilities:**

- 🎯 **Intelligent Planning**: Converts vague programming assignments into step-by-step execution plans
- 📁 **Dynamic File Generation**: Automatically creates and manages project file structures
- 💻 **Code Generation**: Writes complete, functional code in any programming language
- 🧪 **Self-Testing & Debugging**: Built-in testing loop with automatic error correction
- 🔄 **Retry Logic**: Up to 2 test iterations to fix issues before finalizing
- 🧠 **Context Awareness**: Maintains full state of the project across all operations
- 📊 **Checkpointing**: Uses LangGraph's memory checkpointing for state persistence

---

## Architecture Overview

### Tech Stack

- **Language**: Python 3.x
- **Framework**: LangGraph (graph-based workflow orchestration)
- **LLM**: OpenAI-compatible API (configured for Qwen 3.8 Flash)
- **Key Libraries**:
  - `langchain-openai`: LLM integration
  - `langgraph`: Agentic workflow orchestration
  - `pydantic`: Data validation and type checking
  - `python-dotenv`: Environment configuration

### High-Level Architecture

```
User Input (Programming Assignment)
         ↓
    [PLANNER]  → Creates structured execution plan
         ↓
    [ROUTER]   → Determines next step (file/code/test/exit)
         ↓
    [FILE] → Creates project files
    [CODER] → Writes code
    [TESTER] → Tests and validates
         ↓
    [EXIT]  → Finalizes and exits
```

---

## How the Agent Works

### 1. **Planning Phase** 📋

The agent receives a programming assignment and creates a detailed step-by-step plan:

- Analyzes the requirements
- Determines programming language(s)
- Breaks down into discrete tasks: `file` creation, `code` writing, and `test` execution
- Outputs a structured plan with special markers for each step type

**System Prompt Highlights:**
- Creates clear file creation instructions
- Specifies which code sections to write
- Defines testing procedures
- Ensures all files are created before moving to the next file

### 2. **Routing Phase** 🛣️

A router node examines each plan instruction and determines its type:

- **`file`** → Route to file creation handler
- **`code`** → Route to code writing handler
- **`test`** → Route to testing handler
- **`exit`** → End execution

### 3. **File Management** 📁

When a `file` instruction is encountered:

- The agent uses LLM-based reasoning to extract the file path
- Uses the `create_file` tool to generate files with parent directories
- Stores the file path for later code writing
- No manual directory creation needed (parent folders auto-created)

### 4. **Code Generation** 💾

When a `code` instruction is encountered:

- The agent writes complete, production-ready code
- Strips markdown formatting (backticks) from LLM output
- Saves code directly to the previously created file
- Optionally integrates feedback from failed tests

**Coder Features:**
- Writes only relevant code (if asked for HTML, doesn't add unnecessary CSS/JS)
- Accepts test feedback and refines code accordingly
- Maintains code in agent state for reference

### 5. **Testing & Validation** ✅

When a `test` instruction is encountered:

- The agent acts as a code reviewer analyzing the generated code
- Evaluates for:
  - Correctness and functionality
  - Logical efficiency
  - Potential bugs or issues
- Returns `True` if code is production-ready
- Returns detailed feedback if improvements needed

**Testing Logic:**
- Up to 2 test iterations per file (retry limit)
- Failed tests loop back to the coder for refinement
- Passes feedback to coder for targeted improvements
- Auto-passes after 2 iterations regardless of status

### 6. **Exit Phase** 🎉

When an `exit` instruction is encountered:

- Finalizes all outputs
- Saves complete project state
- Ends execution

---

## Workflow Diagram

```
START
  ↓
┌─────────────────────────┐
│    PLANNER              │ ← Takes assignment, creates structured plan
│    - Analyze task       │   Output: [file: X, code: Y, test: Z, exit]
│    - Create plan        │
│    - Determine language │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│    ROUTER               │ ← Reads next instruction
│    - Check plan[instr]  │   Determines: file|code|test|exit
│    - Route accordingly  │
└──────────┬──────────────┘
           ↓
    ┌──────┴──────┬─────────┬─────────┐
    ↓             ↓         ↓         ↓
   FILE         CODE      TEST      EXIT
    ↓             ↓         ↓         ↓
  Create      Generate  Validate   END
  Files       Code      Output
    ↓             ↓         ↓
    └─────────────┼─────────┘
                  ↓
            ROUTER (loop)
                  ↓
            (next instruction)
```

---

## Installation

### Prerequisites

- Python 3.8+
- OpenAI-compatible API key (e.g., TokenHarbor for Qwen)
- pip or conda

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/jakeeeee15/langgraph-coder-agent.git
   cd langgraph-coder-agent
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Or manually install:
   ```bash
   pip install python-dotenv langchain-openai langgraph pydantic langchain
   ```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
HARBOUR_API_KEY=your_api_key_here
```

### Customize the LLM

Edit the LLM configuration in `agent.py`:

```python
llm = ChatOpenAI(
    model="qwen3.8-flash:free",  # Change model here
    api_key=os.environ.get("HARBOUR_API_KEY"),
    base_url="https://tokenharbor.ai/v1",  # Change API base here
    temperature=0  # Deterministic output
)
```

---

## Usage

### Basic Usage

1. **Create your assignment file** (`question.txt`):

   ```
   Make a website with light/dark mode toggle
   Include animations and scroll effects
   Save as index.html, style.css, script.js
   ```

2. **Run the agent**:
   ```bash
   python agent.py
   ```

3. **Watch the execution** stream in real-time with:
   - Planning phase output
   - File creation confirmations
   - Code generation status
   - Test feedback and refinements

### Example Output

```
Starting execution...

--- [PLANNER] ---
Plan.txt has been made...

--- [ROUTER] ---
Routing to file

--- [FILE] ---
Made the file

--- [CODER] ---
Writing code in the background...
index.html has been generated and written successfully

--- [TESTER] ---
Code validated successfully

--- [ROUTER] ---
(continues through all plan steps)

--- Finished Execution ---
```

---

## Project Structure

```
langgraph-coder-agent/
├── agent.py                 # Main agent implementation
├── question.txt             # Input: Programming assignment
├── plan.txt                 # Output: Generated execution plan
├── graph.png                # Visualization of the LangGraph workflow
├── README.md                # This file
└── generated_files/         # Output directory for all created files
    ├── index.html
    ├── style.css
    ├── script.js
    └── ...
```

---

## Agent States & Components

### AgentState (Pydantic Model)

Maintains the complete state throughout execution:

| Field | Type | Purpose |
|-------|------|---------|
| `msgs` | `list[BaseMessage]` | Conversation history for LLM context |
| `language` | `str` | Programming language for generated code |
| `plan` | `list[str]` | Structured execution plan steps |
| `instr` | `int` | Current instruction index in plan |
| `exec_type` | `str` | Type of current instruction (file/code/test/exit) |
| `file_path` | `str` | Path of current file being processed |
| `comments` | `str` | Test feedback for code refinement |
| `ran_successfully` | `bool` | Test result status |
| `code` | `str` | Accumulated code across all files |
| `test_count` | `int` | Number of test iterations for current file |

### Node Functions

| Node | Purpose | Inputs | Outputs |
|------|---------|--------|---------|
| **planner** | Creates execution plan | User assignment | Plan + language |
| **router** | Determines next step | Current instruction | Execution type |
| **file** | Creates project files | File instruction | File path |
| **coder** | Writes code | Code instruction + feedback | Generated code |
| **tester** | Validates code | Generated code | Pass/fail + feedback |
| **exit** | Finalizes execution | Completion | End state |

---

## Workflow Steps

### Complete Execution Flow

1. **User Input** → Assignment text loaded from `question.txt`

2. **Planning**:
   - LLM analyzes requirements
   - Creates numbered plan with `file:`, `code:`, `test:`, `exit:` prefixes
   - Saves plan to `plan.txt`

3. **Iteration Loop** (for each plan step):
   - **Router** reads instruction at index `instr`
   - Routes to appropriate handler
   - Handler processes and increments `instr`

4. **File Creation**:
   - Router recognizes `file:` prefix
   - Calls file manager
   - Creates file with auto-mkdir for parents

5. **Code Generation**:
   - Router recognizes `code:` prefix
   - Coder receives instruction
   - Generates complete code for language
   - Strips markdown formatting
   - Writes to file

6. **Testing**:
   - Router recognizes `test:` prefix
   - Tester analyzes code quality
   - Returns `True` (pass) or feedback (fail)
   - On fail: loops back to coder for refinement
   - Max 2 iterations, then auto-pass

7. **Completion**:
   - Router recognizes `exit:` prefix
   - Exits the execution loop
   - All files saved to disk

---

## Example: Building a Portfolio Website

**Input Assignment** (`question.txt`):
```
Create a modern portfolio website with the following:
- Responsive design
- Light/dark mode toggle
- Smooth animations
- Contact form
- Project showcase section
Use HTML, CSS, and JavaScript
```

**Agent Execution**:

1. **Planner** → Creates plan:
   ```
   file: src/index.html
   code: Write semantic HTML structure for portfolio with sections for hero, projects, contact
   file: src/style.css
   code: Create modern CSS with animations, dark mode support, responsive grid layout
   file: src/script.js
   code: Write JavaScript for dark mode toggle, form validation, scroll animations
   test: Validate all files work together correctly
   exit
   ```

2. **Agent executes** each step, testing and refining until complete

3. **Output**: Fully functional portfolio website ready to deploy

---

## Extending the Agent

### Add Custom Tools

```python
from langchain_core.tools import tool

@tool
def your_custom_tool(parameter):
    """Your tool description"""
    # Implementation
    return result
```

Then bind to LLM:
```python
llm_with_tools = llm.bind_tools([your_custom_tool])
```

### Modify LLM Behavior

Adjust system prompts in:
- `planner()` function for planning logic
- `coder()` function for code generation style
- `tester()` function for validation criteria

### Change Execution Logic

Modify conditional edges in the graph builder:
```python
builder.add_conditional_edges("tester", get_tester_output, {
    True: "router",
    False: "coder"  # On fail, go back to coder
})
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API key errors | Verify `HARBOUR_API_KEY` in `.env` file |
| File permission errors | Check directory write permissions |
| Plan not generating | Verify LLM connection and API quota |
| Code not writing | Ensure file paths are valid and writable |
| Tests failing repeatedly | Increase `test_count` limit or adjust system prompts |

---

## Future Enhancements

- 🔌 Plugin system for custom tools
- 📊 Web UI for real-time monitoring
- 💾 Database persistence instead of in-memory
- 🔍 Code quality metrics and reporting
- 🌐 Multi-model LLM support with fallback
- 📈 Performance optimization and caching

---

## License

MIT License - Feel free to use, modify, and distribute

---

## Author

**Jake** - [GitHub](https://github.com/jakeeeee15)

---

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

---

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [LangChain](https://github.com/langchain-ai/langchain)
- LLM via [TokenHarbor](https://tokenharbor.ai/)

---

**Happy coding! 🚀**
