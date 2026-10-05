import requests
import datetime
import json
import csv
import os


def main():
    queries = ['q1', 'q2', 'q3']
    url = "https://query.wikidata.org/sparql"
    headers = {
        "User-Agent": "mkr1/1.0",
        "Accept": "application/sparql-results+json"
    }

    for q_name in queries:
        file_name = f"{q_name}.rq"
        if not os.path.exists(file_name):
            print(f"Файл {file_name} не знайдено")
            continue

        with open(file_name, "r", encoding="utf-8") as f:
            query = f.read()

        print(f"Виконується запит {q_name}")
        response = requests.get(url, params={"query": query}, headers=headers)

        if response.status_code == 200:
            data = response.json()
            bindings = data.get('results', {}).get('bindings', [])
            vars_list = data.get('head', {}).get('vars', [])

            with open(f"{q_name}.csv", "w", encoding="utf-8", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(vars_list)
                for row in bindings:
                    writer.writerow([row.get(v, {}).get('value', '') for v in vars_list])

            print(f"Результат збережено у {q_name}.csv. Отримано рядків: {len(bindings)}")
        else:
            print(f"Помилка запиту {q_name}: HTTP {response.status_code}")
            print(response.text)

    meta_data = {
        "retrieved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("meta.json", "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=4, ensure_ascii=False)
    print("Час виконання збережено у meta.json")


if __name__ == "__main__":
    main()