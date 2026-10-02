import os
import glob
import numpy as np
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_and_chunk_texts(data_dir: str):
    files = glob.glob(f"{data_dir}/*.txt")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", "!", "?", " ", ""]
    )

    chunks = []
    chunk_metadata = []

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            file_chunks = text_splitter.split_text(text)
            for i, chunk_text in enumerate(file_chunks):
                chunks.append(chunk_text)
                chunk_metadata.append({"source": os.path.basename(file_path), "chunk_id": i})

    return chunks, chunk_metadata


def setup_chromadb(chunks, metadata):
    client = chromadb.PersistentClient(path="./chroma_db")

    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text",
    )
    try:
        client.delete_collection(name="coi_collection")
    except:
        pass

    collection = client.create_collection(name="coi_collection", embedding_function=ollama_ef)

    ids = [f"chunk_{i}" for i in range(len(chunks))]

    print("Генерація ембедингів та збереження у ChromaDB... (це займе трохи часу)")
    collection.add(documents=chunks, metadatas=metadata, ids=ids)
    return collection


def tfidf_search(query, chunks, top_k=3):
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(chunks + [query])

    cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()

    top_indices = cosine_similarities.argsort()[-top_k:][::-1]

    results = []
    for idx in top_indices:
        if cosine_similarities[idx] > 0:
            results.append((chunks[idx], cosine_similarities[idx]))
    return results


def main():
    print("1. Завантаження та розбиття тексту...")
    chunks, metadata = load_and_chunk_texts("data")
    print(f"Створено {len(chunks)} чанків.")

    print("\n2. Індексація в ChromaDB (Векторний пошук)...")
    chroma_collection = setup_chromadb(chunks, metadata)

    queries = [
        # Запит 1 (Точний факт):
        "Room number that Lumian booked at the Auberge du Coq Doré?",
        # Запит 2 (Синонімічний/Синтезний):
        "Why was madame Magician's messenger annoyed when she took Lumian’s letter?",
        # Запит 3 (Описовий/Подієвий):
        "How did the Lumian get past the checkpoint into Trier?"
    ]

    for query in queries:
        print(f"\n{'=' * 50}\nЗАПИТ: '{query}'\n{'=' * 50}")

        print("\nВекторний пошук(ChromaDB + nomic-embed-text)")
        vector_results = chroma_collection.query(query_texts=[query], n_results=2)
        for i, doc in enumerate(vector_results['documents'][0]):
            print(f"[{i + 1}] {doc[:150]}...\n")

        print("\nКлючовий пошук (TF-IDF)")
        keyword_results = tfidf_search(query, chunks, top_k=2)
        if not keyword_results:
            print("Збігів не знайдено (0 спільних слів).")
        for i, (doc, score) in enumerate(keyword_results):
            print(f"[{i + 1}] (score: {score:.3f}) {doc[:150]}...\n")


if __name__ == "__main__":
    main()