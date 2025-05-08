# LangGraph를 활용한 AI Agent 개발

- 강의 목차 중 코드 작성을 하지 않는 회차는 포함되지 않았습니다

## 목차

### 2. LangGraph 기초
- 2.1 LangChain vs LangGraph (feat. LangGraph 개념 설명)
- 2.2 간단한 Retrieval 에이전트 (feat. PDF 전처리 꿀팁)
- 2.3 공식문서 따라하며 실패하는 Agentic RAG
- 2.4 생성된 답변을 여러번 검증하는 Self-RAG
- 2.5 웹 검색을 지원하는 Corrective RAG
- 2.6 SubGraph: LangGraph Agent를 Node로 활용하는 방법
- 2.7 병렬 처리를 통한 효율 개선 (feat. 프롬프트 엔지니어링)
- 2.8 Multi-Agent 시스템과 RouteLLM

### 3. 도구(Tool) 활용과 고급 기능
- 3.1 Workflow vs "찐" Agent (코드 없는 이론설명)
- 3.2 LangChain에서 도구(tool) 활용 방법
- 3.3 LangGraph에서 도구(tool) 활용 방법
- 3.4 LangGraph 내장 도구(tool)를 활용해서 만드는 Agent
- 3.5 Agent의 히스토리를 관리하는 방법
- 3.6 human-in-the-loop: 사람이 Agent와 소통하는 방법
- 3.7 "찐" Multi-Agent System (feat. create_react_agent)

### 5. Model Context Protocol(MCP)
- 5.2 커스텀 MCP 서버 개발방법.py
- 5.3.1 공식문서의 MCP Client 활용방법 I (feat. MultiServerMCPClient).ipynb
- 5.3.2 공식문서의 MCP Client 활용방법 II (feat. ClientSession).ipynb
- 5.4 공식문서에 없는 MCP Client 활용방법.ipynb

## 시작하기

1. 저장소 클론:

```bash
git clone https://github.com/jasonkang14/inflearn-langgraph-agent
```

2. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

3. 노트북 실행 옵션:
- CURSOR:
    ```bash
    cursor run (강의에서는 cursor .)
    ```
- VSCode:
    ```bash
    code .
    ```
- Jupyter Notebook:
    ```bash
    jupyter notebook
    ```

## 요구사항

- Python 3.11+
- 기타 필요한 패키지는 각 노트북 파일에 명시되어 있습니다

## 라이선스

MIT 라이선스로 배포됩니다.

## Streamlit 통합 예제

이 저장소에는 LangGraph와 Streamlit을 통합하는 두 가지 예제가 포함되어 있습니다:

### 1. chat.py
이 예제는 LangGraph의 `invoke()` 메서드를 사용하여 Streamlit과 통합하는 방법을 보여줍니다.

주요 특징:
- `graph.invoke()`를 사용하여 한 번에 전체 응답을 생성
- 간단한 구현으로, 스트리밍 없이 전체 응답을 한 번에 표시
- 메시지 히스토리를 세션 상태로 관리
- 에러 처리 및 로딩 상태 표시 포함

### 2. chat_stream.py
이 예제는 LangGraph의 스트리밍 기능을 활용하여 Streamlit과 통합하는 방법을 보여줍니다.

주요 특징:
- `StreamlitCallbackHandler`를 사용하여 실시간 스트리밍 구현
- 토큰 단위로 응답을 생성하고 표시
- 중간 단계와 토큰 생성 과정을 실시간으로 시각화
- Streamlit의 컨텍스트 관리를 위한 고급 설정 포함

두 예제 모두 동일한 기능을 제공하지만, `chat_stream.py`는 더 풍부한 사용자 경험을 제공하며 응답 생성 과정을 실시간으로 확인할 수 있습니다. 이 예제들은 추후 촬영해서 업데이트할 예정입니다.
