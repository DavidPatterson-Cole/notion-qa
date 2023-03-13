import langchain
from langchain.agents import load_tools
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain import OpenAI, LLMChain, VectorDBQAWithSourcesChain, PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import faiss
import pickle
import openai
import ast
import torch
import re
from transformers import AutoTokenizer
import concurrent.futures
import cohere
import os
co = cohere.Client(os.environ.get('COHERE_API_KEY'))


selection = "gmail"
faiss_locations = {"gmail": "faiss", "notion-feb22": "faiss_moonchaser_notion_feb22", "notion-feb23": "faiss_moonchaser_xs_embedding_feb23"}
# question='Is billing paused for Ariel Zeckleman and why? '
# question='Find the emails of Lana Tang, Christina Nemez, Annie Murray, Swetank Pandey, Max Malak, Alex Bonesteel, Sergei Chernyshov, Lara Ivkovic, Andrei Gorbushkin, Renfred C'
# question='Find the LinkedIn of Lana Tang, Christina Nemez, Annie Murray, Swetank Pandey, Max Malak, Alex Bonesteel, Sergei Chernyshov, Lara Ivkovic, Andrei Gorbushkin, Renfred C'
# question='Find the LinkedIn of Lana Tang, Swetank Pandey, Lara Ivkovic'
# question='Find the $ value paid to Eurostar, Calendly, Zapier, Athena. If multiple, record all $ values paid.'
question='Find the $ value paid to Calendly. If multiple, record all $ values paid.'
# question='Find the $ value paid to Deel, Ganesha Dirschka, Eurostar, Air Canada, Airbnb, Upwork, Bench Accounting, Calendly, Notion Labs, Zapier , Athena, Wise, Gusto, Yuan Zhu. If multiple, record all $ values paid.'
# question='Find the $ value paid to Deel, Ganesha Dirschka, Upwork, Calendly, Zapier. If multiple, record all $ values paid.'
# question='What was the date the most recent email was sent from Moe Faroukh, Abby Diamond, Vikas Sakral, Vamsi Motepalli, Hayk Saakian, Sergei Chernyshov, Yatin Sood, Renfred C, Faizan Malik, Cat O\'Brien'
# question='Look up all the February 2021 pandadoc emails and use them to create the list of names from those emails'
# question='Create a list of February clients. Start by looking up all the February 2021 pandadoc emails. When the email says "Contract Completed", at that name to the list of clients.'
faiss_location = ''
for key, value in faiss_locations.items():
    if key == selection:
        faiss_location = value
        break
    # faiss_location = 'faiss_moonchaser_notion_feb22'

print("faiss location", faiss_location)

intermediate_question = ''
# intermediate_question = 'What is Lana Tang\'s LinkedIn url?'

def ask_question(query: str) -> str:
  user_input = input(query)
  return user_input

def vectordb_qa_tool(query: str) -> str:
    # query = "Moe Faroukh most recent email. Current date: 2023-03-10."
    langchain.verbose=True
    """Tool to answer a question."""
    index = FAISS.load_local(faiss_location, OpenAIEmbeddings())

    # Step 1: query FAISS 
    vectors = index.similarity_search(query, k=30)
    # print(f'{vectors=}')
    vectors_text = [vector.page_content for vector in vectors]
    print(f'\n{query=}')
    print("-------FAISS Vectors-------")
    with open('calendly.pkl', 'ab') as f:
      pickle.dump(query, f)
      pickle.dump("-------FAISS Vectors-------", f)
    for i, vector in enumerate(vectors_text):
      formatted_vector = "{}".format(vector.replace("\n", "\\n"))
      with open('calendly.pkl', 'ab') as f:
        pickle.dump(vector, f)
      print(formatted_vector)
      print('\n')
      # if i == 10:
      #   break
    # print(f'FAISS: {vectors_text=}')
    # print(f'{intermediate_question=}')
    # Should I use query or intermediate_question?
    # new_query = query + " most recent email"
    # print(f'{new_query=}')
    reranked_vectors = co.rerank(query=query, documents=vectors_text, top_n=4)
    print("-------ReRanked Vectors-------")
    with open('calendly.pkl', 'ab') as f:
      pickle.dump("-------ReRanked Vectors-------", f)
    for vector in reranked_vectors:
      formatted_vector = "{}".format(vector.document['text'].replace("\n", "\\n"))
      with open('calendly.pkl', 'ab') as f:
        pickle.dump(formatted_vector, f)
        pickle.dump(vector.relevance_score, f)
      print(formatted_vector)
      # print(f'{vector=}')
      print(vector.relevance_score)
      print('\n')

    # clean_vectors = ''
    answers = []
    print_template = True
    # for vector in vectors_text:
    for vector in reranked_vectors:
      # clean_vectors += f'{vector.page_content}\n'
      rerank_text = vector.document['text']
      # print(f'{rerank_text=}\n')
      answer_prompt_template = """
Given the following extracted parts of a long document and a task, create a final answer.
If you don't know how to complete the task, just say that you don't know. Don't try to make up an answer.

Task 1: Look up all the March 2022 documents and use them to create a list of LinkedIn URLs
Document 1: \"""
Content: SUBJECT: Re: Moonchaser Contract via PandaDoc|EMAIL_FROM: Fahima Ahmed Khan Etha <etha4u@gmail.com>|RECEIVED DATE: Mon, 28 Dec 2020 20:37:40 -0500|CONTENT: >>> LinkedIn is a website to grow professionally
Source: Re: Moonchaser Contract via PandaDoc1
Content: David's LinkedIn is https://www.linkedin.com/in/david-lee-5b1b4b1b/
Source: Re: Moonchaser Contract via PandaDoc1
Content: "Jun Li" document has been completed by all participants.Open the document via https//docs.transactional.pandadoc.com/c/eJx1j09vwjAMxT8Nua0iTlPKIQdYx6ZJTNrGKOIymSSF8CcJbVgRn34pEhI7TLasp58lv-fW1bvGo9TfRonduj3PX8ty97woeJt_tPl7KJEYAX2gfQBOh7FoQpPB44SPnopsPCgY0FHWS_uhRtugDMZZ3CcerULlZCLdgWwEl7TiTOVZimwlFWiqEdiKgYQBT3NG9mITgm96bNSDSWz0_s-NDl03LM7ITgdtQxP12-y8MHUxPB2Llwrm08qXzfKLuHqN1lywi9O9Nv5Mp8VMnS7H7bZa8LGbQ6uWpBYKf4yK8Q_OWbnBRteJcSSIm8dDNPd7HbS6h9YFUxl5PX_HyU10lv8kU0KClln6Czhhfu4--|EMAIL_FROM: PandaDoc <docs@transactional.pandadoc.com>|RECEIVED DATE: Thu, 25 Feb 2021 19:19:11 +0000
Source: Re: "Jun Li" document has been completed by all participants0
Content: None
Source: Your Account Email Change
Content: This is a story about a person, that person has a linkedin: https://www.linkedin.com/in/ganesh-thirumurthi-b9518583/
Source: Story
\"""
Answer 1: https://www.linkedin.com/in/david-lee-5b1b4b1b/, https://www.linkedin.com/in/ganesh-thirumurthi-b9518583/
##
Task 2: {question}
Document 2: \"""
{summaries}
\"""
"""

      # if print_template:
      #     print("--------------------answer prompt template (before filling) --------------------- \n")
      #     print(f'{answer_prompt_template=}' + '\n\n')
      #     print_template = False
      answer_prompt_template = answer_prompt_template.replace("{question}", intermediate_question)
      answer_prompt_template = answer_prompt_template.replace("{summaries}", rerank_text)
      # answer_prompt_template = answer_prompt_template.replace("{summaries}", vector.page_content)
      response = openai.Completion.create(
        model="text-davinci-003",
        prompt=answer_prompt_template,
        max_tokens=128,
        temperature=0
      )['choices'][0]['text']
      # print("--------------------answer prompt template--------------------- \n")
      # print(f'{answer_prompt_template=}' + '\n')
      # print("--------------------re-rank text--------------------- \n")
      # print(f'{rerank_text=}' + '\n')
      # print("--------------------response--------------------- \n")
      # print(f'{response=}'  + '\n')
      answers.append(response)
    return answers

def requests_tool_placeholder(query: str):
  # print('Tried to use Requests. Not implemented yet.')
  return 'Requests not implemented'


def agent(question):
  global intermediate_question
  intermediate_question = question
  print(f'{question=}' + '\n')
  tools = [
      Tool(
          name = "vector_db_qa",
          func=vectordb_qa_tool,
          description="Access contextual information such as emails, documents, databases. This should be the first place to look for information."
      ),
      Tool(
          name="ask_question",
          func=ask_question,
          description="If something is unclear, ask a question about it"
      )

  ]
      #   Tool(
      #     name = "requests_tool_placholder",
      #     func=requests_tool_placeholder,
      #     description="Use this when you need to get content from a website. Input should be an existing url, do not guess a url, and the output will be all the text on that page. Only use this if you are highly confident of the URL input - do not try to guess a URL."
      # ),

  # load tools returns a list of tools but I don't want to add a list to a list, so I just add the first element
  # tools.append(load_tools(["requests"])[0])

  agent_prompt_template = """
Complete the following tasks as best you can. You have access to the following tools:

vector_db_qa: Access contextual information such as emails, documents, databases. This should be the first place to look for information.
ask_question: If something is unclear, ask a question about it

If you are unable to complete the task, just say I don't know. Don't try to make up an answer. Always respond with the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [vector_db_qa, ask_question]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

EXAMPLES:
Question: Which clients did we work with in March 2022?
Thought: What does client mean in this context?
Action: ask_question
Action Input: What does client mean in this context?
Observation: I don't know
Thought: I now know the final answer
Final Answer: I don't know

Question: Look up all the March 2022 documents and use them to create a list of LinkedIn URLs
Thought: I need to use the vector_db_qa tool to find the emails and then extract the linkedin
Action: vector_db_qa
Action Input: March 2022 linkedin
Observation: https://www.linkedin.com/in/david-lee-5b1b4b1b/, https://www.linkedin.com/in/ganesh-thirumurthi-b9518583/
Thought: I now know the final answer
Final Answer: https://www.linkedin.com/in/david-lee-5b1b4b1b/, https://www.linkedin.com/in/ganesh-thirumurthi-b9518583/

Begin!"

Question: {input}
{agent_scratchpad}
"""
  # agent_prompt_template = agent_prompt_template.replace("{input}", question)
  llm_chain = LLMChain(llm=OpenAI(temperature=0), prompt=PromptTemplate(input_variables=["input", "agent_scratchpad"],template=agent_prompt_template))

  tool_names = [tool.name for tool in tools]
  # tool_names = ["vector_db_qa", "requests_tool_placeholder"]
  agent = ZeroShotAgent(llm_chain=llm_chain, allowed_tools=tool_names, return_intermediate_steps=True)

  agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, max_iterations=10)

  return agent_executor.run(question)


def multipleEntities(question):
  prompt_template_1 = """
You must extract the entities from the input question and return two things: 1) the entities in a list 2) the "Question Structure", which is the original question with a placeholder for the entities.

Question: What is the population of New York City and Paris? 
Answer:["New York City", "Paris"]--|--What is the population of (entity)?

Question: Where does David Patterson-Cole, Ganesh Thirumurthi, Josh Bitonte, and Julia Di Spirito live?
Answer:["David Patterson-Cole", "Ganesh Thirumurthi", "Josh Bitonte", "Julia Di Spirito"]--|--Where does (entity) live?

Question: {question}
Answer:
"""
  prompt_template_1 = prompt_template_1.replace("{question}", question)
  response = openai.Completion.create(
    model="text-davinci-003",
    # model="text-curie-001",
    prompt=prompt_template_1,
    max_tokens=500,
    temperature=0
  )['choices'][0]['text']
  print(response)
  entities, question = response.split("--|--")
  # print (f'{entities=}')
  list_entities = ast.literal_eval(entities.strip())
  print (f'{list_entities=}')
  print (f'{question=}')
  # iterate through array calling agent with the current element
  final_answer = []
  for element in list_entities:
    formatted_question = question.replace("(entity)", element)
    final_answer.append(agent(formatted_question))
  # return the aggregate result
  print (f'{final_answer=}')

def main():

  # agent(question) # question is pulled from the global scope

  multipleEntities(question)
  # vectordb_qa_tool("Deel Payment")

main()