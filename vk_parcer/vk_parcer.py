import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_search_url(query: str) -> str:
    base_url = 'https://vk.com/groups?act=catalog&c%5Blike_hints%5D=1&c%5Bper_page%5D=40&c%5Bq%5D='
    section = '&c%5Bsection%5D=communities'
    return base_url + query + section


def extract_labeled_texts(soup: BeautifulSoup) -> list:
    labeled_divs = soup.find_all('div', class_='labeled')
    return [div.get_text() for div in labeled_divs]


def parse_community_info(labeled_texts: list) -> list:
    info = []
    group = []
    for c in labeled_texts:
        if c.strip() == '':
            continue
        group.append(c.strip())

        # Обработка специального случая
        if c.strip() == 'Госорганизация':
            group[-1] = 'Госорганизация'

        # Объединение названия и типа, если нет численности
        if len(group) == 3 and not ('подписч' in c or 'участник' in c):
            group[-2] = f"{group[-2]}, {group[-1]}"
            group.pop()

        # Завершение блока при обнаружении численности
        if 'подписч' in c or 'участник' in c:
            info.append(group)
            group = []
    return info


def extract_community_links(soup: BeautifulSoup) -> list:
    stop_list = {
        '', 'games', '/', '/video', '/join', '/restore', '/audio', 'video', '//vkvideo.ru',
        '/groups/recommendations', 'services', 'apps', '/mobile?utm_source=menu',
        '/legal/recommendations', '/groups?act=catalog',
        *(f'/groups?act=catalog&c[category]={i}' for i in range(0, 33)),
        '/about', '/support?act=home', '/terms',
        '/biz?utm_source=vk_inside&utm_medium=authorization',
        'https://dev.vk.com', '/jobs', '/verify', '/services', '/games'
    }

    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href not in stop_list and not href.startswith('http'):
            links.append('https://vk.com' + href)

    return links[::2]


def combine_info_with_links(info: list, links: list) -> list:
    result = []
    for i in range(len(info)):
        info[i].insert(0, str(i+1))
        result.append(info[i])
        result[i].append(links[i])
    return result


def build_dataframe(community_data: list) -> pd.DataFrame:
    columns = ['№', 'Название', 'Тип сообщества', 'Численность', 'Ссылка']
    data = {col: [] for col in columns}
    for row in community_data:
        for i, col in enumerate(columns):
            data[col].append(row[i] if i < len(row) else '-')
    return pd.DataFrame(data)


def fetch_communities_for_query(query: str) -> pd.DataFrame:
    url = get_search_url(query)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    labeled_texts = extract_labeled_texts(soup)
    info = parse_community_info(labeled_texts)
    links = extract_community_links(soup)
    combined = combine_info_with_links(info, links)
    return build_dataframe(combined)


def collect_user_queries() -> list:
    queries = []
    print("Укажите слова, по которым будет осуществляться поиск групп (через Enter; чтобы закончить ввод - введите 0):")
    while True:
        word = input().strip()
        if word == '0':
            break
        if word:
            queries.append(word)
    return queries


def get_output_path() -> str:
    return input(
        "Укажите путь, куда сохранится таблица excel\n"
        "(пример записи - C:/Users/andry/Downloads/parcer.xlsx, где parcer.xlsx - таблица с будущими данными); учтите слеш: "
    ).strip()


def save_to_excel(dataframes: dict, path: str):
    with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def main():
    path = get_output_path()
    queries = collect_user_queries()

    results = {}
    for query in queries:
        print(f"Обработка запроса: {query}")
        try:
            df = fetch_communities_for_query(query)
            results[query] = df
        except Exception as e:
            print(f"Ошибка при обработке запроса '{query}': {e}")
            results[query] = pd.DataFrame(columns=['№', 'Название', 'Тип сообщества', 'Численность', 'Ссылка'])

    save_to_excel(results, path)
    print(f"Результаты сохранены в: {path}")


if __name__ == "__main__":
    main()
