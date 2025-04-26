from typing import Dict, Any
from langgraph.graph import StateGraph
from models.schema import WorkflowState
from agents.retriever import RetrievalAgent
from agents.reasoner import ReasoningAgent
from agents.formatter import FormatterAgent

class ConversationalWorkflow:
    def __init__(self):
        """Initialize the workflow with all required agents."""
        self.retrieval_agent = RetrievalAgent()
        self.reasoning_agent = ReasoningAgent()
        self.formatter_agent = FormatterAgent()
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the workflow graph."""
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("retrieve", lambda x: self.retrieval_agent(x))
        workflow.add_node("reason", lambda x: self.reasoning_agent(x))
        workflow.add_node("format", lambda x: self.formatter_agent(x))
        
        workflow.add_edge("retrieve", "reason")
        workflow.add_edge("reason", "format")
        
        workflow.set_entry_point("retrieve")
        workflow.set_finish_point("format")
        
        return workflow.compile()

    async def add_document(self, content: str, filename: str) -> None:
        """Add a document to the retrieval agent's vector store."""
        await self.retrieval_agent.add_document(content, filename)

    def execute(self, query: str) -> Dict[str, Any]:
        """Execute the conversation workflow."""
        try:
            initial_state: WorkflowState = {
                "query": query,
                "retrieved_docs": None,
                "source_names": None,
                "reasoning_output": None,
                "response": None,
                "metadata": None
            }

            final_state = self.workflow.invoke(initial_state)

            return {
                "response": {
                    "answer": final_state["response"],
                    "sources": final_state["source_names"]
                }
            }
        except Exception as e:
            raise Exception(f"Workflow execution failed: {str(e)}")