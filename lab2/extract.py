import os
import json
import glob
from enum import Enum
from pydantic import BaseModel, Field
import ollama



# 1. Схема сутностей та зв'язків
class EntityType(str, Enum):
    CHARACTER = "Character"
    LOCATION = "Location"
    PATHWAY_SEQUENCE = "Pathway_Sequence"
    ORGANIZATION = "Organization"
    ITEM_ARTIFACT = "Item_Artifact"


class RelationType(str, Enum):
    VISITED = "VISITED"
    POSSESSES = "POSSESSES"
    INTERACTED_WITH = "INTERACTED_WITH"
    AFFILIATED_TO = "AFFILIATED_TO"
    KNOWS_ABOUT = "KNOWS_ABOUT"


class Entity(BaseModel):
    name: str = Field(description="Exact entity name (e.g., Lumian Lee, Auberge du Coq Dore)")
    entity_type: EntityType = Field(description="Type of entity")
    description: str = Field(description="Short context or description")


class Relationship(BaseModel):
    subject: str = Field(description="Name of the first entity")
    predicate: RelationType = Field(description="Type of relationship")
    target: str = Field(description="Name of the second entity")
    context: str = Field(description="Details of the connection")


class DocumentKnowledge(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]


# 2. Логіка екстракції

def extract_facts_from_text(text: str) -> DocumentKnowledge:

    prompt = f"""
        Analyze the following text fragment from the novel 'Circle of Inevitability'. 
        Extract only the most important entities and their relationships (max 20 most critical relationships).
        Pay attention to:
        - Locations (e.g., cities, Auberge du Coq Doré room numbers).
        - Character interactions (fights, conversations).
        - Mysticism details (Pathways, Sequences).

        Text to analyze:
        {text}
        """

    response = ollama.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': prompt}],
        format=DocumentKnowledge.model_json_schema(),
        options={
            'temperature': 0.0,
            'num_predict': 4096,
            'num_ctx': 8192
        }
    )

    response_text = response['message']['content']
    return DocumentKnowledge.model_validate_json(response_text)


def main():
    data_dir = "data"
    all_facts = []

    files = glob.glob(f"{data_dir}/*.txt")
    if not files:
        print("Помилка: не знайдено .txt файлів у папці 'data'.")
        return

    print(f"Знайдено файлів: {len(files)}. Починається екстракція локально")

    for file_path in files:
        print(f"Обробка файлу: {file_path}... ")
        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read()

            try:
                knowledge = extract_facts_from_text(text_content)

                for rel in knowledge.relationships:
                    all_facts.append({
                        "source_file": os.path.basename(file_path),
                        "subject": rel.subject,
                        "predicate": rel.predicate.value,
                        "target": rel.target,
                        "context": rel.context
                    })
                print(f"  -> Знайдено зв'язків: {len(knowledge.relationships)}")
            except Exception as e:
                print(f"  -> Помилка при обробці {file_path}: {e}")

    with open("facts.json", "w", encoding="utf-8") as f:
        json.dump(all_facts, f, indent=4, ensure_ascii=False)

    print(f"\nЕкстракція завершена. Збережено {len(all_facts)} фактів у facts.json.")


if __name__ == "__main__":
    main()