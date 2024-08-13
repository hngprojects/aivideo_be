from api.utils.settings import settings
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

class SummaryService():
    
    def __init__(self):
        super().__init__()
    
    def init_chain(self):
        prompt_template = """Write a concise summary of the following:
        "{text}"
        CONCISE SUMMARY:"""
        prompt = PromptTemplate.from_template(prompt_template)
        llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k", openai_api_key=settings.OPENAI_API_KEY)
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        return llm_chain

    def summarize_pdf(self, pdf_file):
        """Returns a summarized version of a PDF

        Args:
            pdf_file (str): This is expecting the path to the pdf file

        Returns:
            str: Summary of uploaded PDF file
        """
        
        loader = PyPDFLoader(pdf_file)
        documents = loader.load_and_split()
        
        # Initialize LLM chain
        llm_chain = self.init_chain()
        stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")
        
        # Summarize each chunk individually
        summaries = []
        for doc in documents:
            # Ensure doc is a dict with the right keys
            inputs = {"input_documents": [doc]}
            result = stuff_chain.invoke(inputs)
            summary = result.get("output_text", "")
            summaries.append(summary)

        # Combine all the chunk summaries into the final summary
        final_summary = " ".join(summaries)
        return final_summary


summary_service = SummaryService()
