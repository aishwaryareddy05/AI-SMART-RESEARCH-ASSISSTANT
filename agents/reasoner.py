from typing import Dict, Any
from models.schema import WorkflowState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from tavily import TavilyClient
from config.configurations import get_settings

settings = get_settings()

# === Reasoning Agent ===
class ReasoningAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3
        )

        self.tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)

        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a smart AI assistant. Use only the provided context to answer the user's question.\n\nContext:\n{context}"),
            ("user", "{query}")
        ])

        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are an intent classifier for an AI assistant. Based on the user's query and context, classify the INTENT as one of the following:

- summarize
- extract_kpis
- generate_report
- search_web
- reason

Return ONLY the intent (one of the above) with no explanation.
"""),
            ("user", "Query: {query}\nContext: {context}")
        ])

    def summarize(self, content: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system",  """You are a summarization expert.

Summarize the following content in a clear and concise way, ensuring the key ideas and important highlights are covered. Follow this format:

1. Introduction : Brief overview of the content.
2. Key Points : Bullet points highlighting the most important aspects of the content.
3. Conclusion : A summary of the key takeaway from the content.

Ensure each section is concise, objective, and informative. Make sure they are in bullet points.
"""),
            ("user", "{content}")
        ])
        messages = prompt.format_messages(content=content[:3000])
        response = self.llm.invoke(messages)
        return response.content

    def extract_kpis(self, content: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert analyst. Extract all key performance indicators (KPIs) from the given document. Be concise and bullet them."),
            ("user", "{content}")
        ])
        messages = prompt.format_messages(content=content[:2000])
        response = self.llm.invoke(messages)
        return response.content

    def generate_report(self, topic: str, context: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system","""You are a professional report writer.

Using the provided context, write a well-structured, point-by-point report on the given topic. Follow this exact format:

1. Introduction: Brief overview of the topic.
2. Key Findings:Bullet points highlighting the main findings from the context.
3. Insights: Analysis and observations derived from the findings.
4. Implications: What the findings imply for the business, research, or audience.
5. Recommendations: Actionable suggestions or next steps.

Ensure each section is concise, objective, and informative. Make sure they are in bullet points.
"""),
            ("user", "Topic: {topic} Context:{context}")
        ])
        messages = prompt.format_messages(topic=topic, context=context[:3000])
        response = self.llm.invoke(messages)
        return response.content

    def search_web(self, query: str) -> str:
        try:
            results = self.tavily.search(query=query, max_results=5)
            summary = "\n".join([f"- {res['title']} ({res['url']})" for res in results.get("results", [])])
            return f"Top results for '{query}':\n{summary}"
        except Exception as e:
            return f"Web search failed: {str(e)}"

    def infer_intent(self, query: str, context: str) -> str:
        messages = self.intent_prompt.format_messages(query=query, context=context[:1000])
        intent_response = self.llm.invoke(messages)
        intent = intent_response.content.strip().lower()

        if intent not in ["summarize", "extract_kpis", "generate_report", "search_web", "reason"]:
            return "reason"
        return intent

    def __call__(self, state: WorkflowState) -> WorkflowState:
        try:
            context = "\n".join(state["retrieved_docs"]) if state["retrieved_docs"] else ""
            query = state["query"]

            # Step 1: Infer intent using LLM
            intent = self.infer_intent(query, context)

            # Step 2: Execute the tool or fallback reasoning
            if intent == "summarize":
                output = self.summarize(context)

            elif intent == "extract_kpis":
                output = self.extract_kpis(context)

            elif intent == "generate_report":
                output = self.generate_report(query, context)

            elif intent == "search_web":
                search_results = self.search_web(query)
                output = self.summarize(search_results)

            else:
                # General reasoning using LLM with structured response
                messages = self.response_prompt.format_messages(context=context, query=query)
                response = self.llm.invoke(messages)
                output = response.content

            state["reasoning_output"] = output
            return state

        except Exception as e:
            raise Exception(f"Error in reasoning agent: {str(e)}")
