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

class PlannerOut(BaseModel):
    plan : list[str] = Field(description='the plan ', default_factory=list)
    lang : str = Field(description="the name of the language of the code and nothing else")


def planner(state : AgentState):
    system_prompt = SystemMessage("You are a very systematic and thorough planner "
                                  "You generate step by step plans for every task. "
                                  "for each problem u must give the proper steps "
                                  "Each question should have the list of files that it should make, first word of this line should be 'file' "
                                  "Each question shud have a solve part which contains the question, first word of this line should be 'code' "
                                  "A test part to test the code, first line of this should be 'test' "
                                  "First each of each instruction should be 'file' or 'code' or 'test' "
                                  "Each instruction should be given as an element in an array "
                                  "Final instruction should be 'exit' "
                                  "When making files dont specify making folders. All parent folders will be made automatically "
                                  "If the line is of type code, then specify the language for the code to be written "
                                  "For type 'code' u have to write the prompt only and not the code. Make sure that the prompt is thorough. "
                                  "Once u create a file, do everything to it before u move to the next file. Like only after that create the next file "
                                  "IMP : Each line should start with 'code' or 'file' or 'test' or 'exit'"
                                    
                                  )
    msg_in = [system_prompt] + state.msgs
    llm_str = llm.with_structured_output(PlannerOut)
    plan_out = llm_str.invoke(msg_in)

    path = r"plan.txt"

    with open(path, 'w') as file:
        for p in plan_out.plan:
            file.write(p + "\n")
    print("Plan.txt has been made...", flush=True)

    return {
        'msgs' : [AIMessage(content=str(plan_out.plan))],
        'plan' : plan_out.plan,
        'language' : plan_out.lang,
        'instr' : 0
    }



def router(state : AgentState):
    try:
        plan = state.plan
        step = plan[state.instr]
        exec_type = step[0:4]
        print(f'Routing to {exec_type}', flush=True)
        return {
            "exec_type" : exec_type
        }
    except IndexError:
        return {
            "exec_type" : "exit"
        }

def routing_function(state : AgentState):
    return state.exec_type

def coder(state : AgentState):
    system_prompt = SystemMessage(f"You are an expert coder"
                                  f"You write very good and concise code"
                                  f"You give only the code as output, the full complete working code as a string"
                                  f"You only give out the code and not even a single line other than that : Very Important. "
                                  f"Make sure u only write what is relevant to u. Like if its given to write the HTML, then write HTML only without css or js")
    if state.comments != "":
        step = state.code + '\n' + state.comments
        msg_in = [system_prompt] + [HumanMessage(state.code + "This is the code written so far. Use it for reference\n\n" + step)]

        out = llm.invoke(msg_in)
        raw_code = out.content.strip()
        clean_code = re.sub(r"^```[a-zA-Z]*\n|```$", "", raw_code, flags=re.MULTILINE).strip()

        return {
            "instr": state.instr ,
            "msgs": [out],
            "code": clean_code,
            "comments": ""
        }

    plan = state.plan
    step = plan[state.instr]
    msg_in = [system_prompt] + [HumanMessage(step)]



    out = llm.invoke(msg_in)
    raw_code = out.content.strip()
    clean_code = re.sub(r"^```[a-zA-Z]*\n|```$", "", raw_code, flags=re.MULTILINE).strip()

    with open(state.file_path, 'w') as file:
        file.write(clean_code)

    print(f"{state.file_path} has been generated and written successfully")
    return {
        "instr" : state.instr+1,
        "msgs" : [out],
        "code": state.code + "\n" + clean_code,
        "comments" : ""
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



def file_manager(state : AgentState):
    sys_prompt = SystemMessage(
        "You are a file manager"
        ". Use the tools that are given to u"
        "Ur output is the path of the file u just created. Nothing else, no commas no quotes nothing"
    )

    llm_tooled = llm.bind_tools([create_file])

    out = llm_tooled.invoke([sys_prompt, HumanMessage(state.plan[state.instr])])
    file_path = out.content.strip().replace("'", "").replace('"', "")
    file_path_corr=''
    if hasattr(out, "tool_calls") and out.tool_calls:
        for tc in out.tool_calls:
            if tc["name"] == "create_file":
                create_file.invoke(tc["args"])
                file_path = tc["args"].get("path", file_path)

    print("Made the file ")
    return{
        "instr" : state.instr + 1,
        "file_path" : file_path,
        "comments" : ""
    }

def save_comment(state : AgentState, out):
    return {
        "comments" : out

    }

def add_one(state : AgentState):
    return {
        "instr" : state.instr+1
    }


def tester(state : AgentState):
    sys_prompt = SystemMessage(
        "You are an excellent code problem finder and feedback giver"
        "You should carefully analyse the code u get and should properly criticize it"
        "But dont make niche suggestions, like if it'll work properly just output 'True' nothing else"
        "Only make suggestions if the code wont work properly or there is some big inefficiency"
    )

    code = state.code
    out = llm.invoke([sys_prompt, HumanMessage(code)])

    if out.content.strip().lower() == 'true' or state.test_count >= 2:
        print(f"{state.file_path} solved succesfully", flush=True)
        with open(state.file_path, 'w') as file:
            file.write(state.code)
        return {
            "ran_successfully" : True,
            "instr" : state.instr+1,
            "test_count" : 0
        }
    else:
        return {
            "ran_successfully": False,
            "comments" : out.content,
            "test_count" : state.test_count + 1
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
            print(f"\n\n--- [{current_node.upper()}] ---")

            if current_node == "coder":
                print("Writing code in the background...", flush=True)

        if current_node == "coder":
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
        model="qwen3.8-flash:free",
        api_key=os.environ.get("HARBOUR_API_KEY"),
        base_url="https://tokenharbor.ai/v1",
        temperature=0
)

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

with open("question.txt", 'r') as file:
    inp = file.read()

stream_graph_tokens(graph, inp, config)