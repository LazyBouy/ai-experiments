from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal, List, Dict
import random
import json
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from abc import ABC, abstractmethod

# Specify the local language model
local_llm = "llama3:8b"
llm = ChatOllama(model=local_llm, format="json", temperature=0)

# Define the state for our workflow
class ChessBoard(TypedDict):
    board: List[Dict[str, str]]
    valid: bool
    
# Define the base class for Player
class AgentPlayer(ABC):
    def __init__(self, state: ChessBoard, elo: int = 1500, color: Literal["white", "black"] = "white"):
        self.state = state
        self.elo = elo
        self.color : color
        
    @abstractmethod
    def get_prompt_template(self) -> str:
        pass
    
    def correct_previous_move(self)-> ChessBoard:
        if self.color == "white":
            self.state["board"][-1] = {
                    "white": "",
                    "black": ""
                }
        else:
            last_move = self.state["board"][-1]
            self.state["board"][-1] = {
                    "white": last_move["white"],
                    "black": ""
                }
        self.state["valid"] = True
        return self.make_a_move()
    
    def make_a_move(self) -> ChessBoard:
        if self.state["valid"]:
            pass #@TODO
        else:
            return self.correct_previous_move()
    
    