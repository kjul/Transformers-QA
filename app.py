from typing import Dict, Tuple, Any
import streamlit as st
import wikipedia
from transformers import Pipeline
from transformers import pipeline
from PIL import Image
import requests
from io import BytesIO
import json


def get_qa_pipeline() -> Pipeline:
    qa = pipeline("question-answering")
    return qa


def answer_question(pipeline: Pipeline, question: str, paragraph: str) -> Dict:
    data_in = {
        "question": question,
        "context": paragraph
    }
    return pipeline(data_in)


@st.cache
def get_wiki_paragraph(query: str, content: str = "page", selected_language: str = "en") -> Tuple[Any, Any]:
    wikipedia.set_lang(languages[selected_language])
    results = wikipedia.search(query)
    if content == "summary":
        return wikipedia.summary(results[0]), wikipedia.page(results[0]).images[0]
    elif content == "page":
        return wikipedia.page(results[0]).content, wikipedia.page(results[0]).images[0]


def format_text(paragraph: str, start_idx: int, end_idx: int, full: bool = False) -> str:
    if full:
        return paragraph[:start_idx] + "**" + paragraph[start_idx:end_idx] + "**" + paragraph[end_idx:]
    else:
        if start_idx < 300:
            start_paragraph = 0
        else:
            start_paragraph = start_idx - 300
        paragraph = paragraph[start_paragraph:start_idx] + "**" + paragraph[start_idx:end_idx] + "**" + paragraph[end_idx:end_idx+300]
        return paragraph


def get_wiki_image(search_term):
    wiki_url = 'http://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles='
    try:
        result = wikipedia.search(search_term, results=1)
        wkpage = wikipedia.WikipediaPage(title=result[0])
        title = wkpage.title
        response  = requests.get(wiki_url + title)
        json_data = json.loads(response.text)
        img_link = list(json_data['query']['pages'].values())[0]['original']['source']
        return img_link
    except:
        return 0


languages = {
    "English": "en",
    "German": "de",
    "French": "fr",
    "Russian": "ru",
    "Chinese": "zh"
}

if __name__ == "__main__":
    selected_language = st.sidebar.selectbox(label="Language:", options=list(languages))
    text_option = st.sidebar.selectbox(label="Show:", options=["Wikipedia summary", "Wikipedia page"])
    st.title(text_option)
    paragraph_slot = st.empty()
    image_slot = st.empty()
    wiki_query = st.sidebar.text_input("Wikipedia search term:", "Nueremberg")
    question = st.text_input("QUESTION", "When was Nueremberg first mentioned?")
    if wiki_query:
        wiki_search_result = wikipedia.search(wiki_query, results=1)
        wiki_para, wiki_img = get_wiki_paragraph(wiki_search_result, selected_language=selected_language)
        if text_option == "Wikipedia summary":
            paragraph_slot.markdown(get_wiki_paragraph(wiki_search_result, content="summary",
                                                       selected_language=selected_language)[0])
        else:
            paragraph_slot.markdown(wiki_para)
        try:
            response = requests.get(wiki_img)
            img = Image.open(BytesIO(response.content))
            image_slot.image(get_wiki_image(wiki_query), use_column_width=True)
        except Exception as e:
            print(e)
        if question != "":
            pipeline = get_qa_pipeline()
            try:
                answer = answer_question(pipeline, question, wiki_para)
                st.write(answer)
                start_idx = answer["start"]
                end_idx = answer["end"]
                st.write("[...]")
                st.write(format_text(wiki_para, start_idx, end_idx))
                st.write("[...]")
            except Exception as e:
                print(e)
                st.write("You must provide a valid wikipedia paragraph")
