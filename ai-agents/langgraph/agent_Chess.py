import random
import json
import chess

from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal, List, Dict
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from abc import ABC, abstractmethod

LLM_CALL_THRESHOLD_PER_MOVE = 5

class llm_call_limit_exceeded(Exception):
    pass

# Specify the local language model
local_llm = "llama3:8b"
llm = ChatOllama(model=local_llm, format="json", temperature=0)

# Define the state for our workflow
class ChessBoard(TypedDict):
    board: chess.Board
    game_status: str
    moves: List[Dict[str, int]]
    move_count: int

# Define the base class for Player
class AgentPlayer(ABC):
    def __init__(self, state: ChessBoard, elo: int = 1500, color: Literal["white", "black"] = "white"):
        self.state = state
        self.elo = elo
        self.color : color
        
    @abstractmethod
    def get_prompt_template(self) -> str:
        pass        
          
    def move_from_llm(self) -> int:
        count = 1
        while count <= LLM_CALL_THRESHOLD_PER_MOVE:
            board = self.state.get("board")
            move_str = self.invoke_llm_chain()
            if move_str == "draw":
                self.state["game_status"] = "draw_offered"
            elif  move_str == "draw_accepted":
                self.state["game_status"] = "draw_offer_accepted"
            else:
                move = chess.Move.from_uci(move_str)
                if move in board.legal_moves:
                    board.push(move) 
                    
                    if board.is_stalemate():
                        self.state["game_status"] = "draw_stalemate"
                    elif board.is_insufficient_material():
                        self.state["game_status"] = "draw_insufficient_material"
                    elif board.is_fivefold_repetition():
                        self.state["game_status"] = "draw_fivefold_repetition"
                    elif board.is_fivefold_repetition():
                        self.state["game_status"] = "draw_seventyfive_moves"
                    elif board.is_checkmate():
                        self.state["game_status"] = f"win_{self.color}!"
                    
                    moves = self.state.get("moves")
                    if self.color == "white":
                        moves.append(
                            {
                                "white": move_str,
                                "black": ""
                            }
                        )
                        move_count = self.state["move_count"]
                        self.state["move_count"] = move_count + 1
                    else:
                        last_move = moves[-1]
                        last_move["black"] = move_str
                        self.state["moves"][-1] = last_move  
                else:
                    count +=1
        
        if count > LLM_CALL_THRESHOLD_PER_MOVE:
            print ("llm_call_limit_exceeded")
            raise llm_call_limit_exceeded
            
    def invoke_llm_chain(self):
        pass
        
            
        
    
    