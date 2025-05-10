# mcp_stdio_server.py

# 표준 라이브러리 임포트
import os
from datetime import datetime

# 서드파티 라이브러리 임포트
from dotenv import load_dotenv
from langchain import hub
from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.tools import TavilySearchResults
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

# 환경 변수 로드
load_dotenv()

###########################################
# 핵심 컴포넌트 초기화
###########################################

# MCP 서버 초기화
mcp = FastMCP("house_tax")

# 언어 모델 초기화
llm = AzureChatOpenAI(
    azure_deployment='gpt-4o-2024-11-20',
    api_version='2024-08-01-preview',   
    temperature=0
)

small_llm = AzureChatOpenAI(
    azure_deployment='gpt-4o-mini-2024-07-18',
    api_version='2024-08-01-preview',
    temperature=0
)

# 임베딩 및 벡터 저장소 초기화
embedding_function = AzureOpenAIEmbeddings(
    model='text-embedding-3-large',
    azure_endpoint=os.getenv('AZURE_OPENAI_EMBEDDING_ENDPOINT'),
    api_key=os.getenv('AZURE_OPENAI_EMBEDDING_API_KEY')
)

vector_store = Chroma(
    embedding_function=embedding_function,
    collection_name='real_estate_tax',
    persist_directory='./real_estate_tax_collection'
)

retriever = vector_store.as_retriever(search_kwargs={'k': 3})

###########################################
# 유틸리티 함수
###########################################

def format_docs(docs):
    """여러 문서를 하나의 문자열로 결합하는 포맷팅 함수
    
    Args:
        docs: page_content를 포함하는 Document 객체 리스트
        
    Returns:
        str: 줄바꿈으로 구분된 문서 내용을 하나로 합친 문자열
    """
    return "\n\n".join(doc.page_content for doc in docs)

###########################################
# 세금 공제 관련 컴포넌트
###########################################

# RAG 프롬프트 초기화
rag_prompt = hub.pull("rlm/rag-prompt")

def get_market_value_rate_search():
    """현재 연도의 공정시장가액비율을 웹에서 검색합니다"""
    # DuckDuckGo 검색 초기화
    search = TavilySearchResults()

    return search.invoke(f"{datetime.now().year}년도 공정시장가액비율은?")


###########################################
# MCP 도구들
###########################################

@mcp.tool(
    name="tax_deductible_tool",
    description= """사용자의 부동산 소유 현황에 대한 질문을 기반으로 세금 공제액을 계산합니다.
    
    이 도구는 다음 두 단계로 작동합니다:
    1. tax_deductible_chain을 사용하여 일반적인 세금 공제 규칙을 검색
    2. user_deductible_chain을 사용하여 사용자의 특정 상황에 규칙을 적용

    Args:
        question (str): 부동산 소유에 대한 사용자의 질문
        
    Returns:
        str: 세금 공제액 (예: '9억원', '12억원')
    """
)
def tax_deductible_tool(question: str) -> str:
    # 세금 공제 체인 구성
    tax_deductible_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt
        | small_llm
        | StrOutputParser()
    )

    # 기본 공제 질문 정의
    deductible_question = '주택에 대한 종합부동산세 과세표준의 공제액을 알려주세요'

    # 사용자 공제 프롬프트 구성
    user_deductible_prompt = """아래 [Context]는 주택에 대한 종합부동산세의 공제액에 관한 내용입니다. 
    사용자의 질문을 통해서 가지고 있는 주택수에 대한 공제액이 얼마인지 금액만 반환해주세요

    [Context]
    {tax_deductible_response}

    [Question]
    질문: {question}
    답변: 
    """

    user_deductible_prompt_template = PromptTemplate(
        template=user_deductible_prompt,
        input_variables=['tax_deductible_response', 'question']
    )

    user_deductible_chain = (
        user_deductible_prompt_template
        | small_llm
        | StrOutputParser()
    )
    tax_deductible_response = tax_deductible_chain.invoke(deductible_question)
    tax_deductible = user_deductible_chain.invoke({
        'tax_deductible_response': tax_deductible_response, 
        'question': question
    })
    return tax_deductible


@mcp.tool(
    name="tax_base_tool",
    description="""종합부동산세 과세표준을 계산하기 위한 공식을 검색하고 형식화합니다.
    
    이 도구는 RAG(Retrieval Augmented Generation) 방식을 사용하여:
    1. 지식 베이스에서 과세표준 계산 규칙을 검색
    2. 검색한 규칙을 수학 공식으로 형식화

    Returns:
        str: 과세표준 계산 공식
    """
)
def tax_base_tool() -> str:
    tax_base_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt
        | small_llm
        | StrOutputParser()
    )

    tax_base_question = '주택에 대한 종합부동산세 과세표준을 계산하는 방법은 무엇인가요? 수식으로 표현해서 수식만 반환해주세요'
    tax_base_response = tax_base_chain.invoke(tax_base_question)
    return tax_base_response


@mcp.tool(
    name="market_value_rate_tool",
    description="""사용자의 부동산 상황에 적용되는 공정시장가액비율을 결정합니다.
    
    이 도구는:
    1. 현재 공정시장가액비율 정보가 포함된 검색 결과를 사용
    2. 사용자의 특정 상황(보유 부동산 수, 부동산 가치)을 분석
    3. 적절한 공정시장가액비율을 백분율로 반환

    Args:
        question (str): 부동산 소유에 대한 사용자의 질문
        
    Returns:
        str: 공정시장가액비율 백분율 (예: '60%', '45%')
    """
)
def market_value_rate_tool(question: str) -> str:
    market_value_rate_prompt = PromptTemplate.from_template("""아래 [Context]는 공정시장가액비율에 관한 내용입니다. 
    당신에게 주어진 공정시장가액비율에 관한 내용을 기반으로, 사용자의 상황에 대한 공정시장가액비율을 알려주세요.
    별도의 설명 없이 공정시장가액비율만 반환해주세요.

    [Context]
    {context}

    [Question]
    질문: {question}
    답변: 
    """)

    market_value_rate_chain = (
        market_value_rate_prompt
        | small_llm
        | StrOutputParser()
    )

    market_value_rate_search = get_market_value_rate_search()
    market_value_rate = market_value_rate_chain.invoke({
        'context': market_value_rate_search, 
        'question': question
    })
    return market_value_rate


@mcp.tool(
    name="house_tax_tool",
    description="""수집된 모든 정보를 사용하여 최종 종합부동산세액을 계산합니다.
    
    이 도구는 다음 정보들을 결합하여 최종 세액을 계산합니다:
    1. 과세표준 계산 공식
    2. 공정시장가액비율
    3. 공제액
    4. 세율표

    Args:
        tax_base_question (str): 과세표준 계산 공식
        market_value_rate_question (str): 공정시장가액비율
        tax_deductible_question (str): 공제액
        question (str): 부동산 세금 계산에 대한 사용자의 질문
        
    Returns:
        str: 설명이 포함된 최종 세금 계산액
    """
)
def house_tax_tool(tax_base_question: str, market_value_rate: str, tax_deductible: str, question: str) -> str:

    house_tax_prompt = ChatPromptTemplate.from_messages([
        ('system', f'''과세표준 계산방법: {tax_base_question}
        공정시장가액비율: {market_value_rate}
        공제액: {tax_deductible}

        위의 공식과 아래 세율에 관한 정보를 활용해서 세금을 계산해주세요.
        세율: {{tax_rate}}
        '''),
        ('human', '{question}')
    ])

    house_tax_chain = (
        {
            'tax_rate': retriever | format_docs,
            'question': RunnablePassthrough()
        }
        | house_tax_prompt
        | llm
        | StrOutputParser()
    )

    house_tax = house_tax_chain.invoke(question)
    return house_tax


###########################################
# MCP 프롬프트
###########################################


@mcp.prompt(
    name="house_tax_system_prompt",
    description="""종합부동산세 계산 프롬프트"""
)
def house_tax_system_prompt():
    system_message_content = """당신의 역할은 주택에 대한 종합부동산세를 계산하는 것입니다. 
    사용자의 질문이 들어오면, 사용자의 질문을 바탕으로 종합부동산세를 계산해주세요.
    종합부동산세를 계산하기 위해서는 과세표준을 어떻게 계산할지 파악해야하고, 
    사용자에 질문에 따른 공제액을 파악해야 하고, 
    사용자에 질문에 따른 공정시장가액비율을 파악해야 합니다.
    이 세가지를 파악하고 나면, 종합부동산세를 계산해주세요.
    """
    # MCP에는 시스템 프롬프트가 존재하지 않음(2024년 5월기준)
    return base.UserMessage(content=system_message_content)

###########################################
# 메인 진입점
###########################################

if __name__ == "__main__":
    mcp.run(transport="sse")

