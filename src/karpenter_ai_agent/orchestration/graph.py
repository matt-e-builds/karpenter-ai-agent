from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel

from langgraph.graph import StateGraph, END

from karpenter_ai_agent.models import AnalysisInput, ParserOutput, AgentResult, AnalysisReport
from karpenter_ai_agent.agents.parser_agent import ParserAgent
from karpenter_ai_agent.agents.cost_agent import CostAgent
from karpenter_ai_agent.agents.reliability_agent import ReliabilityAgent
from karpenter_ai_agent.agents.security_agent import SecurityAgent
from karpenter_ai_agent.agents.evaluator_agent import EvaluatorAgent
from karpenter_ai_agent.orchestration.aggregate import aggregate_results
from karpenter_ai_agent.rag.explain import attach_contract_explanations


class GraphState(BaseModel):
    input: AnalysisInput
    parser_output: Optional[ParserOutput] = None
    cost_result: Optional[AgentResult] = None
    reliability_result: Optional[AgentResult] = None
    security_result: Optional[AgentResult] = None
    report: Optional[AnalysisReport] = None
    explain_attempts: int = 0


parser_agent = ParserAgent()
cost_agent = CostAgent()
reliability_agent = ReliabilityAgent()
security_agent = SecurityAgent()
evaluator_agent = EvaluatorAgent()


def node_parse(state: GraphState) -> Dict[str, Any]:
    output = parser_agent.run(state.input)
    return {"parser_output": output}


def node_cost(state: GraphState) -> Dict[str, Any]:
    config = state.parser_output.config if state.parser_output else None
    if config is None:
        return {"cost_result": AgentResult()}
    result = cost_agent.run(config, state.input.region, state.input.monthly_spend)
    return {"cost_result": result}


def node_reliability(state: GraphState) -> Dict[str, Any]:
    config = state.parser_output.config if state.parser_output else None
    if config is None:
        return {"reliability_result": AgentResult()}
    result = reliability_agent.run(config)
    return {"reliability_result": result}


def node_security(state: GraphState) -> Dict[str, Any]:
    config = state.parser_output.config if state.parser_output else None
    if config is None:
        return {"security_result": AgentResult()}
    result = security_agent.run(config)
    return {"security_result": result}


def node_aggregate(state: GraphState) -> Dict[str, Any]:
    report = aggregate_results(
        analysis_input=state.input,
        parser_output=state.parser_output,
        cost_result=state.cost_result,
        reliability_result=state.reliability_result,
        security_result=state.security_result,
    )
    return {"report": report}


def _explanations_enabled(state: GraphState) -> bool:
    return bool(state.input.options.get("enable_explanations")) if state.input else False


def _evaluator_enabled(state: GraphState) -> bool:
    return bool(state.input.options.get("enable_evaluator")) if state.input else False


def node_explain(state: GraphState) -> Dict[str, Any]:
    report = state.report
    if report is None:
        return {}
    if not _explanations_enabled(state):
        return {}
    attach_contract_explanations(
        report.issues,
        llm_available=bool(state.input.options.get("enable_explanation_llm")),
    )
    report.raw["explanations_enabled"] = True
    return {"report": report, "explain_attempts": state.explain_attempts + 1}


def node_evaluate(state: GraphState) -> Dict[str, Any]:
    report = state.report
    if report is None:
        return {}
    if not _evaluator_enabled(state):
        return {}

    evaluation = evaluator_agent.run(
        report,
        use_llm=bool(state.input.options.get("enable_evaluator_llm")),
    )
    report.evaluation_notes = evaluation.notes
    report.raw["evaluation_retries"] = evaluation.retries

    if (
        state.input.options.get("enable_reflection")
        and evaluation.notes
        and state.explain_attempts < 1
    ):
        attach_contract_explanations(
            report.issues,
            llm_available=bool(state.input.options.get("enable_explanation_llm")),
        )
        evaluation = evaluator_agent.run(
            report,
            use_llm=bool(state.input.options.get("enable_evaluator_llm")),
        )
        report.evaluation_notes = evaluation.notes
        report.raw["evaluation_retries"] = evaluation.retries + 1
        return {"report": report, "explain_attempts": state.explain_attempts + 1}

    return {"report": report}


def _should_short_circuit(state: GraphState) -> str:
    if not state.parser_output:
        return "continue"
    if state.parser_output.config is None or state.parser_output.parse_errors:
        return "report"
    return "continue"


def build_graph() -> StateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("parse", node_parse)
    graph.add_node("cost", node_cost)
    graph.add_node("reliability", node_reliability)
    graph.add_node("security", node_security)
    graph.add_node("aggregate", node_aggregate)
    graph.add_node("explain", node_explain)
    graph.add_node("evaluate", node_evaluate)

    graph.set_entry_point("parse")
    graph.add_conditional_edges(
        "parse",
        _should_short_circuit,
        {
            "report": "aggregate",
            "continue": "cost",
        },
    )
    graph.add_edge("cost", "reliability")
    graph.add_edge("reliability", "security")
    graph.add_edge("security", "aggregate")
    graph.add_edge("aggregate", "explain")
    graph.add_edge("explain", "evaluate")
    graph.add_edge("evaluate", END)

    return graph


def run_analysis_graph(analysis_input: AnalysisInput) -> AnalysisReport:
    graph = build_graph()
    runnable = graph.compile()
    result = runnable.invoke(GraphState(input=analysis_input))
    report = result["report"]
    return report
