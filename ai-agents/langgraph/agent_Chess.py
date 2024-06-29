import random
import json
import chess

from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal, List, Dict
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.callbacks import BaseCallbackHandler
#from abc import ABC, abstractmethod

LLM_CALL_THRESHOLD_PER_MOVE = 5

# Call Back Handler
class MyCustomHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print(f"My custom handler, token: {token}")

class llm_call_limit_exceeded(Exception):
    pass

# Specify the local language model
local_llm =  "llama3:8b" #"phi3:latest"
llm = ChatOllama(model=local_llm, format="json", temperature=0, callbacks=[MyCustomHandler()])

"""
local_llm = "llama3-70b-8192"
llm = ChatGroq(
    temperature=0,
    model="llama3-70b-8192"
)
"""

# Define the state for our workflow
class ChessBoard(TypedDict):
    board: chess.Board
    current_move: Literal["white", "black"]
    game_status: Literal[
                         "game_in_progress", # game in progress
                         "draw_offered", # game in progress
                         "draw_offer_accepted",
                         "draw_offer_rejected", # game in progress
                         "draw_stalemate",
                         "draw_insufficient_material",
                         "draw_fivefold_repetition",
                         "draw_seventyfive_moves",
                         "win_white",
                         "win_black",
                         ]
    moves: List[Dict[str, int]]
    move_count: int

# Define the base class for Player
class AgentPlayer():
    def __init__(self, state: ChessBoard, elo: int = 1500, color: Literal["white", "black"] = "white"):
        self.state = state
        self.elo = elo
        self.color = color
        
    def get_prompt_template(self) -> str:
        
        return """
            You are a chess player with elo score {elo} and playing the game with {color}.
            The chess board information is in Forsyth-Edwards Notation (FEN) strings below.
            You check the board information (in FEN string) and "move number" very carefully before making the next move.
            Board (in FEN string): {board_str} 
            Move Number: {move_number}
            Status Draw offer: {draw_offer_status}; 
                possible values: 
                    [
                        "none" = no draw offer exist, 
                        "draw_offered" = an open draw offer exists from opponent,
                        "draw_offer_rejected" = your draw offer was rejected by opponent. 
                    ]  
            Your task is to find the best next move in Standard Algebraic Notation (SAN) string.
            Please adhere to the below rules:
            1. You first check "Status Draw Offer". 
            2. If "Status Draw Offer" == "draw_offered" then you may decide to "accept" or "reject" the draw offer, 
            2. You may also offer draw by saying "draw", 
               only if "Status Draw offer" != "draw_offer_rejected" and "Status Draw offer" != "draw_offered".
            3. You may also resign by saying "resign".
            3. You always try to win and make the best move possible. 
            4. Your final output is just a json(no other text) as shown below: 
                {{"decision": (str) <your_move in "SAN string" or "accepted" or "rejected" or "draw" or "resign">}}
        """        
          
    # The Main Execution Function (MEF) for the agent
    # Called ONLY when LLM touchpoint is required
    # LLM touchpoints are required when the game statuses are:
    #  - game_in_progress
    #  - draw_offered
    #  - draw_offer_rejected
    def move_from_llm(self) -> ChessBoard:
        count = 1
        while count <= LLM_CALL_THRESHOLD_PER_MOVE:
            board = self.state.get("board")
            move_str = self.invoke_llm_chain()
            
            # Continue the game with NO-Board update
            if move_str == "draw":
                self.state["game_status"] = "draw_offered"  
            elif  move_str == "accepted":
                self.state["game_status"] = "draw_offer_accepted"
            elif  move_str == "rejected":
                self.state["game_status"] = "draw_offer_rejected"
            elif move_str == "resigned":
                self.state["game_status"] = "win_black" if self.color == "white" else "win_white" 
            else: # Continue the game with Board update
            
                try:
                    # Parse the move using the board's context
                    move = board.parse_san(move_str)
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
                        
                    break
                            
                except (chess.InvalidMoveError, 
                        chess.IllegalMoveError,
                        chess.AmbiguousMoveError):
                    count +=1                      
        
        if count > LLM_CALL_THRESHOLD_PER_MOVE:
            print ("llm_call_limit_exceeded")
            raise llm_call_limit_exceeded
        
        # Change Player if Winner is not yet decided
        if "win_" not in self.state.get("game_status"):
            self.state["current_move"] = "black" if self.color == "white" else "white"
        
        return self.state
        
    def invoke_llm_chain(self) -> str:
        template = self.get_prompt_template()
        prompt = PromptTemplate.from_template(template)
        prompt_format = {
            "elo": self.elo,
            "color": self.color,
            "board_str": self.state.get("board").fen(), 
            "move_number": (self.state.get("move_count") + 1) if self.color == "white" else self.state.get("move_count"),
            "draw_offer_status": self.state.get("game_status") if "draw" in self.state.get("game_status") else "none"
        }
        print(prompt.format_prompt(
            **prompt_format
        ))
        llm_chain = prompt | llm | StrOutputParser()
        generation = llm_chain.invoke(prompt_format)
        data = json.loads(generation)
        """
        Possible move_str
        1. san
        2. accepted
        3. rejected
        4. draw
        5. resigned
        """
        move_str = data["decision"] 
        
        return move_str

class PlayerW(AgentPlayer):
    def __init__(self, state: ChessBoard):
        super().__init__(state=state, color="white")
        
class PlayerB(AgentPlayer):
    def __init__(self, state: ChessBoard):
        super().__init__(state=state, color="black")
        

def transition(state: ChessBoard) -> Literal["white", "black", "end"]:
    if state.get("game_status") in ["game_in_progress", 
                                    "draw_offered", 
                                    "draw_offer_rejected"]:
        return state.get("current_move")
    elif state.get("game_status") in ["draw_offer_accepted",
                                      "draw_stalemate",
                                      "draw_insufficient_material",
                                      "draw_fivefold_repetition",
                                      "draw_seventyfive_moves"]:
        print(f"""Game Tied! Reason: {state.get("game_status")}""")
        return "end"
    else:
        print(f"""Game Decided! Reason: {state.get("game_status")}""")
        return "end"
    
        
# Define the state machine
workflow = StateGraph(ChessBoard)

# Define Nodes
workflow.add_node("agent_white", lambda state: PlayerW(state).move_from_llm())
workflow.add_node("agent_black", lambda state: PlayerB(state).move_from_llm())

workflow.set_entry_point("agent_white")

# Define edges between nodes WHITE -> BLACK
workflow.add_conditional_edges(
    "agent_white",
    transition,
    {
        "black": "agent_black",
        "end": END,
    }
)

# Define edges between nodes BLACK -> WHITE
workflow.add_conditional_edges(
    "agent_black",
    transition,
    {
        "white": "agent_white",
        "end": END,
    }
)

# Initialize the state
initial_state = ChessBoard(
    board=chess.Board(),
    current_move="white",
    game_status = "game_in_progress",
    moves=list(),
    move_count=0
)

# Compile the workflow into a runnable app
app = workflow.compile()

for event in app.stream(initial_state):
    print(event)


        
    
        
    
        
    