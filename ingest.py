"""This is the logic for ingesting Notion data into LangChain."""
from pathlib import Path
from langchain.text_splitter import CharacterTextSplitter
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import pickle


# Here we load in the data in the format that Notion exports it in.
# ps = list(Path("Text/").glob("**/*.txt"))
ps = list(Path("Calendly/").glob("**/*.csv"))


data = []
sources = []
for p in ps:
    with open(p) as f:
        data.append(f.read())
    sources.append(p)

# Here we split the documents, as needed, into smaller chunks.
# We do this due to the context limits of the LLMs.
text_splitter = CharacterTextSplitter(chunk_size=1500, separator="\n")
docs = []
metadatas = []
for i, d in enumerate(data):
    splits = text_splitter.split_text(d)
    docs.extend(splits)
    metadatas.extend([{"source": sources[i]}] * len(splits))


# Here we create a vector store from the documents and save it to disk.
store = FAISS.from_texts(docs, OpenAIEmbeddings(), metadatas=metadatas)
# This creates an index out of the store data structure
faiss.write_index(store.index, "docs.index")
# Now that it's saved to disk, we can remove the index from memory
store.index = None
# This keeps the vectors from the store accessible, but this is not related to the index
with open("faiss_store.pkl", "wb") as f:
    pickle.dump(store, f)
