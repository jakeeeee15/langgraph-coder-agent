import json
import subprocess
import shlex
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing import Annotated, TypedDict
from pydantic import BaseModel, Field
from langchain.messages import SystemMessage, AIMessage, HumanMessage
import sys
from langchain_core.messages import BaseMessage
import os
from langgraph.graph.message import add_messages
import re
from langchain_core.tools import tool
import warnings

warnings.filterwarnings('ignore')


load_dotenv()


class AgentState(BaseModel):
    msgs : Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    language : str = Field(description="Language in which the code has to be written", default="C")
    plan : list[str] = Field(description="The plan where each step is given as a step in an array", default_factory=list)
    instr : int = Field(description="The index of the curr instruction to be executed from the plan list", default=0)
    exec_type : str = Field(description="The type of current instruction", default="")
    file_path : str = Field(description="The file path of the current file which is being edited", default="")
    comments : str = Field(description="The suggestions tester made about the current code", default="")
    ran_successfully : bool = Field(description="Whether the code ran successfully", default=False)
    code : str = Field(description="code that is written do far", default="")
    test_count : int = Field(description="Number of times current code has been tested", default=0)
    test_case : str = Field(description="The test case for the program as a string", default="")
    output_case : str = Field(description="The output that is to be recieved from the terminal when performing the test_case", default="")

class PlannerOut(BaseModel):
    plan : list[str] = Field(description='the plan ', default_factory=list)
    lang : str = Field(description="the name of the language of the code and nothing else")


def planner(state : AgentState):
    system_prompt = SystemMessage(
        "You are an expert software architect and planner.\n"
        "Your task is to break down the user's coding request into a sequence of steps.\n"
        "You must respond with ONLY a valid, raw JSON object (no markdown, no extra text).\n\n"
        "JSON structure:\n"
        "{\n"
        '  "lang": "<Programming Language>",\n'
        '  "plan": [\n'
        '    "file: <path>",\n'
        '    "code: <comprehensive instructions for the entire file>",\n'
        '    "test: <path>",\n'
        '    "exit"\n'
        "  ]\n"
        "   'file_name': <name of the file being accessed>"        
        "}\n\n"
        "Rules:\n"
        "- Group all code generation for a file into a SINGLE 'code:' step right after its 'file:' step.\n"
        "- Do not break a file's code into multiple steps.\n"
        "- Keep the plan concise (between 3 and 7 steps total)."
        "The path given after test is the path of the code that shud be tested\n"
        "Its not necessary that all plans should have all these steps, like u can skip any of the steps. But always fill the file_name field with the file u are accessing. \n"
        "Use the test with the path to simply run the code without writing any code\n"
        "Paths given after file in the plan are the files to be created.\n"
    )

    msg_in = [system_prompt] + state.msgs
    plan_out = llm.invoke(msg_in)
    out = plan_out.content.strip()

    cleaned_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", out, flags=re.MULTILINE).strip()

    try:
        data = json.loads(cleaned_json)
        plan_list = data.get("plan", [])
        lang_str = data.get("lang", state.language)
        file_name = data.get("file_name", "")
        comments = data.get("comments", "")
    except Exception:
        # Fallback: parse lines directly if the JSON string had formatting quirks
        lines = [line.strip("- *0123456789. ") for line in out.splitlines() if line.strip()]
        plan_list = [l for l in lines if any(l.startswith(k) for k in ('file', 'code', 'test', 'exit'))]
        if not plan_list or plan_list[-1] != "exit":
            plan_list.append("exit")
        lang_str = state.language


    path = r"plan.txt"
    print("file name is " + file_name)
    with open(path, 'w') as file:
        for p in plan_list:
            file.write(p + "\n")
    print("Plan.txt has been made...", flush=True)

    return {
        'msgs' : [AIMessage(content=str(plan_list))],
        'plan' : plan_list,
        'language' : lang_str,
        'instr' : 0,
        "file_path" : file_name,
        "comments" : comments
    }



def router(state : AgentState):
    try:
        plan = state.plan
        step = plan[state.instr]
        exec_type = step[0:4]
        print(f'Routing to {exec_type}', flush=True)
        # if exec_type=='file'
        return {
            "exec_type" : exec_type
        }
    except IndexError:
        return {
            "exec_type" : "exit"
        }

def routing_function(state : AgentState):
    return state.exec_type


import json
import re


def coder(state: AgentState):
    system_prompt = SystemMessage(
        "You are an expert coder. You write very good and concise code.\n"
        "You must respond with ONLY a valid, raw JSON object (no markdown formatting, no extra text).\n"
        "The JSON structure must be exactly as follows:\n"
        "{\n"
        '  "code": "<the full complete working code as a string>",\n'
        '  "test_case": "<a sample test case to run against the code. It shud be exactly whats given as input when running the code>"\n'
        '  "output": :<The output that this sample test case should give in the terminal if any. Only give sure outputs, leave it blank if ure unsure of what the output will be>"\n'
        "}\n"
        "Very Important: Do not output anything outside of this JSON object.\n"
        "Make sure you only write what is relevant to the requested file."
        "If there is no input to the program, then leave the testcase place empty"
    )

    print("Reached coder")

    with open("plan.txt") as file:
        plan_text = file.read()

    step = state.plan[state.instr]

    code = ""
    if state.file_path and os.path.exists(state.file_path):
        with open(state.file_path, 'r') as file:
            code = file.read()

    if state.code == "" and code != "":
        state.code = code

    if state.comments != "":
        context_msg = f"{state.code}\nThis is the code written so far.\n\nTester Feedback: {state.comments}\nFix the code based on this feedback."
        next_instr = state.instr
    else:
        context_msg = f"{state.code}\nThis is the code written so far.\n\nPlan:\n{plan_text}\n\nCurrent Task: Do {step}"
        next_instr = state.instr + 1

    msg_in = [system_prompt, HumanMessage(context_msg)]
    out = llm.invoke(msg_in)
    raw_content = out.content.strip()

    cleaned_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()

    try:
        data = json.loads(cleaned_json)
        final_code = data.get("code", "")
        test_case = data.get("test_case", "")
        expected_output = data.get("output", "")
    except json.JSONDecodeError:
        final_code = cleaned_json
        test_case = ""
        expected_output=""

    with open(state.file_path, 'w') as file:
        file.write(final_code)

    print(f"{state.file_path} generated successfully.", flush=True)
    if test_case:
        print(f"Suggested Test: {test_case}", flush=True)

    return {
        "instr": next_instr,
        "msgs": [out],
        "code": final_code,
        "comments": "",
        'test_case' : test_case,
        "output_case" : expected_output
    }

@tool
def create_file(path):
    """function to create a file at the given path"""
    print("Tool file make has been called")
    from pathlib import Path

    pa = Path(path)

    pa.parent.mkdir(parents=True, exist_ok=True)
    pa.touch(exist_ok=True)
    print(f'Created File at {path}', flush=True)


def file_manager(state: AgentState):
    step = state.plan[state.instr].strip()

    match = re.search(r"^file[:\s]+([^\s]+)", step, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip().replace("'", "").replace('"', "")
    else:
        parts = step.split()
        file_path = parts[1] if len(parts) > 1 else "output.txt"

    pa = Path(file_path)
    pa.parent.mkdir(parents=True, exist_ok=True)
    pa.touch(exist_ok=True)

    print(f"Made the file: {file_path}", flush=True)

    return {
        "instr": state.instr + 1,
        "file_path": file_path,
        "comments": "",
        "code": ""
    }


def save_comment(state : AgentState, out):
    return {
        "comments" : out
    }

def add_one(state : AgentState):
    return {
        "instr" : state.instr+1
    }

from pathlib import Path
import subprocess

def run_code(command: str, state:AgentState, timeout: int = 15) -> tuple[bool, str]:
    if not command:
        return False, "No execution command defined for this file type."

    try:
        res = subprocess.run(
            command,
            shell=True,
            input=state.test_case,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if res.returncode == 0:
            out = res.stdout.strip()
            return True, out if out else "Executed successfully with no output."
        else:
            err = res.stderr.strip()
            out = res.stdout.strip()
            msg = err if err else out
            return False, f"Process exited with code {res.returncode}:\n{msg}"

    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout}s (possible infinite loop)."
    except Exception as e:
        return False, f"Execution failed: {str(e)}"

def get_run_command(file_path: str) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()
    stem = path.stem

    commands = {
        ".py": f"python3 {file_path}",
        ".c": f"gcc {file_path} -o temp_{stem} && ./temp_{stem}",
        ".cpp": f"g++ {file_path} -o temp_{stem} && ./temp_{stem}",
        ".js": f"node {file_path}",
        ".ts": f"npx ts-node {file_path}",
        ".sh": f"bash {file_path}",
        ".html": f"xdg-open {file_path}",
        ".java": f"javac {file_path} && java {stem}",
        ".rs": f"rustc {file_path} -o temp_{stem} && ./temp_{stem}",
        ".go": f"go run {file_path}",
    }

    return commands.get(ext, "")

class TestOut(BaseModel):
    comment : str = Field(description="The comments about the code based on the Error it gave if any", default="")
    terminal : bool = Field(description="Can the error be solved by running a terminal command. Example pip installs and all. True if possible thru terminal", default=False)
    cmd : str = Field(description="Exact command to be given to terminal to solve the problem", default="")



def tester(state: AgentState):
    sys_prompt = SystemMessage(
        "You are given the code and the output that it generated. Suggest how to fix it so"
        " that the coder agent can fix it. Make sure that u tell what the error is properly."
    )
    print("Reached tester")
    step = state.plan[state.instr].strip()

    match = re.search(r"^file[:\s]+([^\s]+)", step, re.IGNORECASE)
    if match:
        file_path = match.group(1).strip().replace("'", "").replace('"', "")
    else:
        parts = step.split()
        file_path = parts[1] if len(parts) > 1 else "output.txt"

    run_command = get_run_command(file_path)
    if run_command == '':
        print("Cant run this code. Dont have the knowledge for it")
        return exit_prompt(state)

    ran_bool, output = run_code(run_command, state)

    is_timeout = "Execution timed out" in output
    output_matched = True

    if not state.output_case:
        if ran_bool or is_timeout:
            ran_bool = True
            if is_timeout:
                print(f"Code timed out (likely a game/server loop). Assuming success.", flush=True)
        else:
            output_matched = False
    else:
        if ran_bool:
            actual_stripped = str(output).strip()
            expected_stripped = str(state.output_case).strip()

            if actual_stripped == "Executed successfully with no output.":
                actual_stripped = ""

            if actual_stripped != expected_stripped:
                output_matched = False
                ran_bool = False
                output = f"Code ran without crashing, but logic is wrong.\nExpected Output:\n{expected_stripped}\n\nActual Output:\n{actual_stripped}"
        else:
            output_matched = False

    if ran_bool or state.test_count >= 2:
        if not ran_bool:
            print(f"Gave up on {state.file_path} after multiple failed attempts. Moving on.", flush=True)
        else:
            print(f"{state.file_path} solved successfully", flush=True)

        with open(state.file_path, 'w') as file:
            file.write(state.code)

        return {
            "ran_successfully": True,
            "instr": state.instr + 1,
            "test_count": 0
        }
    else:
        with open(file_path, 'r') as file:
            state.code = file.read()

        prompt = f"{state.code}\n\nThis is the code, and it failed verification:\n{output}"
        llm_str = llm.with_structured_output(TestOut)
        out = llm_str.invoke([sys_prompt, HumanMessage(prompt)])
        if out.terminal:
            print(f"Running '{out.cmd}' in the terminal")
            ran, terminal_out = run_code(out.cmd, state, 20)
            state.test_count+=1
            if state.test_count >= 2:
                print("Terminal fixes exhausted. Returning to coder.", flush=True)
                return {
                    "ran_successfully": False,
                    "comments": f"Attempted terminal command '{out.cmd}' but it didn't solve the issue. Original error:\n{output}",
                    "test_count": state.test_count
                }

            return tester(state)


        return {
            "ran_successfully": False,
            "comments": out.comment,
            "test_count": state.test_count + 1
        }

def exit_prompt(state : AgentState):
    """If the user signals the conversation is over this shud be used to stop the running"""
    print("Byeee...")
    return state


def stream_graph_tokens(graph, user_input: str, config: dict):
    print("\nStarting execution...\n", flush=True)

    current_node = None

    for message_chunk, metadata in graph.stream(
            {"msgs": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="messages",
    ):
        node_name = metadata.get("langgraph_node", "")

        if node_name in ["router", "exit"]:
            continue

        if node_name != current_node:
            current_node = node_name
            print(f"\n\n--- [{current_node.upper()}] ---", flush=True)

            if current_node == "coder":
                print("Writing code in the background ", end="", flush=True)

        if current_node == "coder":
            # Print a single dot for every chunk received to show live progress
            if message_chunk.content:
                sys.stdout.write(".")
                sys.stdout.flush()
            continue

        if message_chunk.content:
            content = message_chunk.content
            if isinstance(content, str):
                sys.stdout.write(content)
                sys.stdout.flush()

    print("\n\n--- Finished Execution ---")

def get_tester_output(state : AgentState):
    return state.ran_successfully



llm = ChatOpenAI(
        model="glm-5.3-flash",
        api_key=os.environ.get("HARBOUR_API_KEY"),
        base_url="https://tokenharbor.ai/v1",
        temperature=0
)

# llm = ChatOpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=os.environ.get("OPENROUTER_API_KEY"),
#     model="google/gemma-4-31b-it:free",
#     temperature=0.1,
#     streaming=False,
#     timeout=120
# )



builder = StateGraph(AgentState)

builder.add_node("planner", planner)
builder.add_node("coder", coder)
builder.add_node("file", file_manager)
builder.add_node("exit", exit_prompt)
builder.add_node("router", router)
builder.add_node("tester", tester)

builder.add_edge(START, "planner")
builder.add_edge("planner", "router")
builder.add_conditional_edges("router", routing_function,
                              {
                                  "file" : "file",
                                  "code" : "coder",
                                  "exit" : "exit",
                                  "test" : "tester"
                              })

builder.add_edge("coder" , "router")
builder.add_edge("file", "router")
builder.add_conditional_edges("tester", get_tester_output,
                              {
                                  True : "router",
                                  False : "coder"
                              }
                              )

builder.add_edge("exit", END)

checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer)

#
# with open("graph.png", "wb") as f:
#     f.write(graph.get_graph().draw_mermaid_png())
# print("Graph saved as graph.png")
#


config = {'configurable' : {'thread_id' : 'assignment_thread1'}}

with open("fix.txt", 'r') as file:
    inp = file.read()

stream_graph_tokens(graph, inp, config)