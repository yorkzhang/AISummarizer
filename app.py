# -*- coding:utf-8 -*-
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from flask import Flask, send_from_directory,request,send_file
from datetime import datetime
import random
import urllib.parse
import os
import azure.cognitiveservices.speech as speechsdk
from langchain.vectorstores import FAISS
from langchain.text_splitter import Document,RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import json

load_dotenv()
app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/dbinit', methods=["POST"])
def dbinit():
    global qa
    global title
    print("Hello AISummarizer!")
        # url = "https://mp.weixin.qq.com/s/SiBQBHvDij8_cvUgAi8H5Q"
    url = request.json.get("url").strip()
    response = requests.get(url)
    html = response.text
    # Parse the webpage content using BeautifulSoup
    soup = BeautifulSoup(html, "html5lib")

    # Get the article title
    title = soup.find(
        "h1", {"class": "rich_media_title", "id": "activity-name"}
    ).get_text()
    # Get the article content
    pcontent = ""
    paragraphs = soup.find_all("p")

    for p in paragraphs:
        pcontent += p.get_text() + "\n"

    secContent = ""
    for section in soup.find_all('section'):
        if section.span:
            secContent += section.span.text + "\n"
        else:
            secContent += section.text+ "\n"
    
    content = pcontent if len(pcontent) > len(secContent) else secContent
    print(content)
    doc = Document(page_content = content)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents([doc])
    
    embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get('OPENAI_API_KEY'), 
                                    openai_api_base=os.environ.get('OPENAI_API_BASE'), 
                                    openai_api_type="azure", 
                                    openai_api_version=os.environ.get('OPENAI_API_VERSION'), 
                                    deployment="ada2", chunk_size=1)
    

    docsearch = FAISS.from_documents(docs, embeddings)
    

    llmchat = AzureChatOpenAI(
        temperature=0,
        deployment_name="gpt3_5",
        model_name="gpt-35-turbo",
    )
    qa = RetrievalQA.from_chain_type(llm=llmchat, chain_type="stuff", retriever = docsearch.as_retriever() )
    print("init completed")
    return "init completed"

@app.route("/gettitle", methods=["GET"])
def get_title():
    global title
    return title


@app.route("/ask", methods=["POST"])
def ask():
    global qa
    print("Ask question now!")
    query = request.json.get("query")
    isOOB = request.json.get("isOOB")
    query_name = request.json.get("queryname")
    if(isOOB == "true"):
        query = getOOBQuery(query_name)
    print(query)
    answer = qa.run(query)
    print(answer)
    return answer

def getOOBQuery(query_name):
    query_string = ""
    with open('oob_queries.json') as f:
        data = json.load(f)
    query_list =[]
    for query in data:
        query_list.append(query)
    
    for query in query_list:
        if(query["name"] == query_name):
            query_string= query["details"]
            break
    return query_string

@app.route('/text-to-speech', methods=['Get','POST'])
def text_to_speech():
    if(request.method == 'POST'):
        print("I will speak now!")
        text = request.json['text']
        url = request.json['url']
        path = urllib.parse.urlparse(url).path
        last_part = path.split("/")[-1]

        random_number = str(random.randint(1000, 9999))
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = last_part + random_number + current_time + ".mp3"
        speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
        audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)
        speech_config.speech_synthesis_voice_name='	zh-CN-XiaoxiaoNeural'
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesized for text [{}]".format(text))
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print("Error details: {}".format(cancellation_details.error_details))
                    print("Did you set the speech resource key and region values?")
        response = send_file(filename, as_attachment=True)
        return response
    else:
        return ""


if __name__ == '__main__':
    app.run()