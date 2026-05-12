from langgraph.graph import StateGraph,END
from langchain_groq import ChatGroq
from typing import TypedDict,List
from app.sentiment import analyze,get_sentiment_label
from app.database import create_table,insert_result,get_latest_by_ticker
import json
import os

class AgentState(TypedDict):
    question:str
    tickers:List[str]
    question_type:str
    raw_data:dict
    conviction:dict
    narrative:str
    final_response:dict
    
def parse_intent(state: AgentState) -> AgentState:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    prompt = f"""You are a financial assistant.
Given this question: {state["question"]}

Extract and return ONLY valid JSON with these keys:
  tickers: list of NSE ticker symbols mentioned (e.g. ["INFY", "HDFC"])
  question_type: one of "single", "compare", "market"

If no specific ticker is mentioned, set question_type to "market" and tickers to [].
Return ONLY the JSON. No explanation. No extra text."""

    response = llm.invoke(prompt)
    
    try:
        parsed = json.loads(response.content)
        state["tickers"] = parsed.get("tickers", [])
        state["question_type"] = parsed.get("question_type", "market")
    except:
        state["tickers"] = []
        state["question_type"] = "market"
    
    return state

def fetch_and_score(state:AgentState) -> AgentState:
    DEFAULT_TICKERS = ["INFY","RELIANCE", "HDFC", "TCS", "WIPRO"]
    
    tickers = state["tickers"] if state["tickers"] else DEFAULT_TICKERS
    
    raw_data = {}
    conviction = {}
    
    for ticker in tickers:
        rows = get_latest_by_ticker(ticker)
        
        if  not rows:
            continue
        raw_data[ticker] = rows
        
        scores = [row["weighted_score"] for row in rows]
        avg_score = sum(scores)/len(scores)
        
        labels = [row["sentiment"] for row in rows]
        signal = max(set(labels),key=labels.count)
        
        conviction[ticker] = {
            "score": round(avg_score,3),
            "signal" : signal,
            "headline_count" : len(rows)
        }
    state["raw_data"]= raw_data
    state["conviction"] = conviction
    return state

def generate_narrative(state: AgentState)->AgentState:
    llm = ChatGroq(
        model = "llama-3.1-8b-instant",
        api_key = os.getenv("GROQ_API_KEY")
    )
    context = ""
    for ticker,data in state["conviction"].items():
        rows = state["raw_data"].get(ticker,[])
        headlines = [row["headline"] for row in rows[:3]]
        context += f"{ticker}: {data['signal']} (score: {data['score']}) based on {data['headline_count']} headlines\n"
        context += f"Sample headlines: {headlines}\n\n"
    prompt = f"""You are a financial analyst helping an Indian retail investor.
Question: {state["question"]}

Here is the sentiment data — use ONLY this, do not make anything up:
{context}

Answer in exactly 3 sentences:
1. What the signal is
2. Why (based on the headlines)
3. A direct answer to the question"""

    response = llm.invoke(prompt)
    state["narrative"] = response.content
    return state

def format_response(state: AgentState)->AgentState:
    state["final_response"] = {
        "question" : state["question"],
        "tickers_analyzed" : state["tickers"],
        "conviction" : state["conviction"],
        "narrative" : state["narrative"]
    }
    return state

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("parse_intent", parse_intent)
    graph.add_node("fetch_and_score", fetch_and_score)
    graph.add_node("generate_narrative", generate_narrative)
    graph.add_node("format_response", format_response)

    graph.set_entry_point("parse_intent")

    graph.add_edge("parse_intent", "fetch_and_score")
    graph.add_edge("fetch_and_score", "generate_narrative")
    graph.add_edge("generate_narrative", "format_response")
    graph.add_edge("format_response", END)

    return graph.compile()

app = build_graph()

def run_agent(question:str)->dict:
    initial_state = AgentState(
        question=question,
        tickers=[],
        question_type="",
        raw_data={},
        conviction={},
        narrative="",
        final_response={}
    )
    result = app.invoke(initial_state)
    return result["final_response"]