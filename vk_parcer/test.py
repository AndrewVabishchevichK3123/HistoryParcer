import unittest
from bs4 import BeautifulSoup
from vk_parcer import (
    get_search_url,
    extract_labeled_texts,
    parse_community_info,
    extract_community_links,
    combine_info_with_links
)

class TestVKCommunityParser(unittest.TestCase):

    def test_get_search_url_correctly_encodes_query(self):
        # Arrange
        query = "python"
        expected = "https://vk.com/groups?act=catalog&c%5Blike_hints%5D=1&c%5Bper_page%5D=40&c%5Bq%5D=python&c%5Bsection%5D=communities"

        # Act
        result = get_search_url(query)

        # Assert
        self.assertEqual(result, expected)

    def test_extract_labeled_texts_returns_text_from_labeled_divs(self):
        # Arrange
        html = '<div class="labeled">Название</div><div class="labeled">Тип</div><div class="other">Игнор</div>'
        soup = BeautifulSoup(html, "html.parser")

        # Act
        result = extract_labeled_texts(soup)

        # Assert
        self.assertEqual(result, ["Название", "Тип"])

    def test_parse_community_info_handles_standard_and_edge_cases(self):
        # Arrange
        labeled_texts = [
            "Python-программисты",
            "Сообщество",
            "150 тыс. подписчиков",
            "Минцифры России",
            "Госорганизация",
            "2.1 млн участников"
        ]

        # Act
        result = parse_community_info(labeled_texts)

        # Assert
        expected = [
            ["Python-программисты", "Сообщество", "150 тыс. подписчиков"],
            ["Минцифры России", "Госорганизация", "2.1 млн участников"]
        ]
        self.assertEqual(result, expected)

    def test_parse_community_info_handles_missing_subscriber_count_gracefully(self):
        # Arrange
        labeled_texts = ["Название", "Тип", "Госорганизация"]  # нет численности → не завершится

        # Act
        result = parse_community_info(labeled_texts)

        # Assert
        # Поскольку нет строки с "подписч"/"участник", блок не добавляется
        self.assertEqual(result, [])

    def test_extract_community_links_filters_and_builds_absolute_urls(self):
        # Arrange
        html = '''
        <a href="/python_community"></a>
        <a href="/video"></a>
        <a href="/groups?act=catalog&c[category]=5"></a>
        <a href="/mincifry"></a>
        '''
        soup = BeautifulSoup(html, "html.parser")

        # Act
        result = extract_community_links(soup)

        # Assert
        # Ожидаем только валидные ссылки, без stop_list, и с префиксом
        # Также учитываем [::2] — берем каждый второй элемент
        # Вход: ['/python_community', '/mincifry'] → после [::2] → ['/python_community']
        self.assertEqual(result, ["https://vk.com/python_community"])

    def test_combine_info_with_links_matches_by_index_and_adds_number(self):
        # Arrange
        info = [
            ["Группа 1", "Сообщество", "100 подписчиков"],
            ["Группа 2", "Госорганизация", "50 участников"]
        ]
        links = ["https://vk.com/group1", "https://vk.com/group2"]

        # Act
        result = combine_info_with_links(info, links)

        # Assert
        expected = [
            ["1", "Группа 1", "Сообщество", "100 подписчиков", "https://vk.com/group1"],
            ["2", "Группа 2", "Госорганизация", "50 участников", "https://vk.com/group2"]
        ]
        self.assertEqual(result, expected)

    def test_combine_info_with_links_handles_mismatched_lengths_gracefully(self):
        # Arrange
        info = [["A", "B", "C"]]
        links = []  # меньше ссылок

        # Act & Assert
        with self.assertRaises(IndexError):
            combine_info_with_links(info, links)
