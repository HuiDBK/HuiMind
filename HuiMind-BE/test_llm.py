from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.embeddings import DashScopeEmbeddings

from src.settings import (
    model_name,
    openai_api_key,
    openai_api_base,
    embedding_api_base,
    dashscope_api_key,
    embedding_model_name,
)


def test_llm_chat():
    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=openai_api_key,
        openai_api_base=openai_api_base,
        temperature=0,
    )

    response = llm.invoke("你好，简单介绍一下你自己")

    print("LLM response:", response.content)


def test_embedding():
    embeddings = DashScopeEmbeddings(
        model=embedding_model_name,
        dashscope_api_key=dashscope_api_key,
    )

    vector = embeddings.embed_query("今天天气不错")

    print("Embedding length:", len(vector))
    print("Embedding sample:", vector[:5])


if __name__ == "__main__":
    test_llm_chat()
    # test_embedding()

