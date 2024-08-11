from api.db.database import get_db
from api.utils.settings import settings
from api.utils.file_upload import upload_file
from langchain.document_loaders import PyPDFLoader
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
        loader = PyPDFLoader(pdf_file)
        documents = loader.load()
        print(documents)

        llm_chain = self.init_chain()
        stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")

        summary = stuff_chain.invoke(documents)["output_text"]

        return summary


summary_service = SummaryService()