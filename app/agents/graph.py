from langgraph.graph import END, START, StateGraph

from app.agents.nodes.context_node import context_node
from app.agents.nodes.discovery_node import discovery_node
from app.agents.nodes.explanation_node import explanation_node
from app.agents.nodes.report_node import report_node
from app.agents.nodes.risk_node import risk_node
from app.agents.state import AgentState


def build_graph():
    """
    LangGraph Workflow를 구성한다.

    실행 순서:
    START
      → Discovery Node
      → Context Analysis Node
      → Risk Scoring Node
      → Explanation Node
      → Report Node
      → END
    """

    graph = StateGraph(AgentState)

    graph.add_node("discovery", discovery_node)
    graph.add_node("context_analysis", context_node)
    graph.add_node("risk_scoring", risk_node)
    graph.add_node("explanation", explanation_node)
    graph.add_node("report", report_node)

    graph.add_edge(START, "discovery")
    graph.add_edge("discovery", "context_analysis")
    graph.add_edge("context_analysis", "risk_scoring")
    graph.add_edge("risk_scoring", "explanation")
    graph.add_edge("explanation", "report")
    graph.add_edge("report", END)

    return graph.compile()