import json
import networkx as nx
import community as community_louvain
from pyvis.network import Network
import ollama
import chromadb
import chromadb.utils.embedding_functions as embedding_functions


# 1. Завантаження фактів та побудова графа
def build_and_visualize_graph(json_path="facts.json", output_html="graph.html"):
    with open(json_path, "r", encoding="utf-8") as f:
        facts = json.load(f)

    G = nx.Graph()

    for fact in facts:
        sub = fact['subject']
        tar = fact['target']
        rel = fact['predicate']
        G.add_edge(sub, tar, label=rel, title=fact.get('context', ''))

    print(f"Побудовано граф: {G.number_of_nodes()} вузлів, {G.number_of_edges()} ребер.")

    partition = community_louvain.best_partition(G)

    for node, community_id in partition.items():
        G.nodes[node]['group'] = community_id
        G.nodes[node]['title'] = f"Community {community_id}"

    net = Network(notebook=False, height="800px", width="100%", bgcolor="#222222", font_color="white")
    net.from_nx(G)

    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100)
    net.save_graph(output_html)
    print(f"Візуалізацію графа збережено у файл: {output_html}")

    return G, partition, facts



# 2. GraphRAG: Генерація резюме спільнот

def generate_community_summaries(partition, facts):
    communities_data = {}
    for node, c_id in partition.items():
        if c_id not in communities_data:
            communities_data[c_id] = []

    for fact in facts:
        sub, tar = fact['subject'], fact['target']
        if sub in partition:
            c_id = partition[sub]
            communities_data[c_id].append(fact)

    summaries = []
    print("\nГенерація резюме для знайдених спільнот...")

    for c_id, c_facts in communities_data.items():
        if len(c_facts) < 2:
            continue

        facts_text = "\n".join(
            [f"- {f['subject']} {f['predicate']} {f['target']} ({f.get('context', '')})" for f in c_facts[:20]])

        prompt = f"""
        You are an expert on the 'Circle of Inevitability' novel.
        Summarize the storyline, main themes, and connections of the following cluster of entities:
        {facts_text}
        Keep the summary concise (max 3-4 sentences).
        """

        response = ollama.chat(model='llama3.1', messages=[{'role': 'user', 'content': prompt}],
                               options={'temperature': 0.1})
        summaries.append(f"Community {c_id} Summary: {response['message']['content']}")
        print(f"  -> Згенеровано резюме для спільноти {c_id}")

    return summaries



# 3. Виконання запитів та порівняння (Reduce / Standard RAG)
def answer_with_graphrag(question, summaries):
    all_summaries_text = "\n\n".join(summaries)
    prompt = f"""
    Based on the following community summaries from a Knowledge Graph, answer the question comprehensively.
    Question: {question}

    Graph Summaries:
    {all_summaries_text}
    """
    response = ollama.chat(model='llama3.1', messages=[{'role': 'user', 'content': prompt}],
                           options={'temperature': 0.2})
    return response['message']['content']


def answer_with_standard_rag(question):
    client = chromadb.PersistentClient(path="./chroma_db")
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings", model_name="nomic-embed-text"
    )
    collection = client.get_collection(name="coi_collection", embedding_function=ollama_ef)

    results = collection.query(query_texts=[question], n_results=5)
    chunks_text = "\n\n---\n\n".join(results['documents'][0])

    prompt = f"""
    Based on the following text excerpts, answer the question comprehensively.
    Question: {question}

    Excerpts:
    {chunks_text}
    """
    response = ollama.chat(model='llama3.1', messages=[{'role': 'user', 'content': prompt}],
                           options={'temperature': 0.2})
    return response['message']['content']


def main():

    G, partition, facts = build_and_visualize_graph()

    # Синтезне питання
    question = "How are Lumian, Madam Magician, and Osta Trul connected, and why did Lumian trip him up after their first meeting?"

    print(f"\nГлобальне питання:\n{question}\n")

    summaries = generate_community_summaries(partition, facts)
    print("\n[Генерація фінальної відповіді через GraphRAG...]")
    graphrag_answer = answer_with_graphrag(question, summaries)
    print("\nGraphRAG")
    print(graphrag_answer)


    print("\n[Генерація фінальної відповіді через Standard RAG...]")
    standard_rag_answer = answer_with_standard_rag(question)
    print("\nStandard RAG")
    print(standard_rag_answer)


if __name__ == "__main__":
    main()