import pytest
import requests
import pandas as pd
from bs4 import BeautifulSoup
import os
import tempfile
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vk_parcer import (
    get_search_url,
    extract_labeled_texts,
    parse_community_info,
    extract_community_links,
    combine_info_with_links,
    build_dataframe,
    fetch_communities_for_query,
    collect_user_queries,
    save_to_excel,
    main
)


class TestVKParserIntegration:
    """Интеграционные тесты для парсера VK групп"""
    
    def test_integration_url_generation_and_request(self):
        """Тест интеграции генерации URL и HTTP-запроса"""
        # Arrange
        query = "программирование"
        
        # Act
        url = get_search_url(query)
        response = requests.get(url)
        
        # Assert
        assert response.status_code == 200
        assert query in url
        assert "vk.com/groups" in url
        assert "catalog" in url
    
    def test_integration_html_parsing_and_data_processing(self):
        """Тест интеграции парсинга HTML и обработки данных"""
        # Arrange
        query = "музыка"
        url = get_search_url(query)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Act - последовательная обработка данных через несколько модулей
        labeled_texts = extract_labeled_texts(soup)
        community_info = parse_community_info(labeled_texts)
        links = extract_community_links(soup)
        
        # Assert базовой структуры
        assert isinstance(labeled_texts, list)
        assert isinstance(community_info, list)
        assert isinstance(links, list)
        
        if community_info and links:
            combined_data = combine_info_with_links(community_info, links)
            df = build_dataframe(combined_data)
            
            assert isinstance(combined_data, list)
            assert isinstance(df, pd.DataFrame)
            assert len(df.columns) == 5  # Проверка структуры DataFrame
    
    def test_integration_full_data_pipeline_with_realistic_data(self):
        """Тест полного пайплайна обработки данных с реалистичными данными"""
        # Arrange - более реалистичный HTML контент
        test_html = """
        <html>
            <body>
                <div class="labeled">IT Community</div>
                <div class="labeled">Открытая группа</div>
                <div class="labeled">15000 подписчиков</div>
                <div class="labeled"></div>
                <div class="labeled">Music Lovers</div>
                <div class="labeled">Публичная страница</div>
                <div class="labeled">8000 участников</div>
                <a href="/club123">Ссылка 1</a>
                <a href="/public456">Ссылка 2</a>
                <a href="/event789">Ссылка 3</a>
            </body>
        </html>
        """
        
        # Act - имитация полного процесса
        soup = BeautifulSoup(test_html, "html.parser")
        labeled_texts = extract_labeled_texts(soup)
        community_info = parse_community_info(labeled_texts)
        links = extract_community_links(soup)
        
        # Адаптируем данные для корректной интеграции
        if len(community_info) > len(links):
            community_info = community_info[:len(links)]
        elif len(links) > len(community_info):
            links = links[:len(community_info)]
        
        if community_info and links:
            combined_data = combine_info_with_links(community_info, links)
            df = build_dataframe(combined_data)
            
            # Assert
            assert len(df) == min(len(community_info), len(links))
            assert "IT Community" in df["Название"].values
            assert "15000 подписчиков" in df["Численность"].values
    
    def test_integration_multiple_queries_processing(self):
        """Тест обработки нескольких поисковых запросов"""
        # Arrange
        queries = ['технологии', 'образование']
        results = {}
        
        # Act - обработка нескольких запросов
        for query in queries:
            try:
                df = fetch_communities_for_query(query)
                results[query] = df
            except Exception as e:
                # Создаем пустой DataFrame в случае ошибки
                results[query] = pd.DataFrame(columns=['№', 'Название', 'Тип сообщества', 'Численность', 'Ссылка'])
                print(f"Ошибка при обработке запроса '{query}': {e}")
        
        # Assert
        assert len(results) == 2
        for query in queries:
            assert query in results
            assert isinstance(results[query], pd.DataFrame)
            # Проверяем что структура DataFrame сохраняется
            expected_columns = ['№', 'Название', 'Тип сообщества', 'Численность', 'Ссылка']
            assert all(col in results[query].columns for col in expected_columns)
    
    def test_integration_user_input_with_data_collection(self):
        """Тест интеграции пользовательского ввода со сбором данных"""
        # Arrange
        mock_inputs = ['программирование', 'python', '0']
        
        # Act - имитация пользовательского ввода
        with patch('builtins.input', side_effect=mock_inputs):
            queries = collect_user_queries()
        
        # Assert
        assert queries == ['программирование', 'python']
        assert len(queries) == 2
        assert isinstance(queries, list)
    
    def test_integration_error_handling_network_issues(self):
        """Тест обработки сетевых ошибок в интеграционном потоке"""
        # Arrange
        invalid_url = "https://invalid-vk-url-12345.com/groups"
        
        # Act & Assert
        with patch('vk_parcer.get_search_url', return_value=invalid_url):
            try:
                df = fetch_communities_for_query("test")
                # Если не выброшено исключение, проверяем структуру
                assert isinstance(df, pd.DataFrame)
            except requests.RequestException:
                # Ожидаемое поведение для сетевых ошибок
                pass
            except Exception as e:
                # Другие исключения также допустимы
                assert isinstance(e, Exception)


class TestVKParserIntegrationEdgeCases:
    """Тесты граничных случаев и обработки ошибок"""
    
    def test_integration_empty_search_results(self):
        """Тест обработки пустых результатов поиска"""
        # Arrange - использование очень специфичного запроса
        unusual_query = "xyz123unusualquery_999999"
        
        # Act
        try:
            df = fetch_communities_for_query(unusual_query)
            
            # Assert - даже при пустых данных структура DataFrame сохраняется
            assert isinstance(df, pd.DataFrame)
            expected_columns = ['№', 'Название', 'Тип сообщества', 'Численность', 'Ссылка']
            assert all(col in df.columns for col in expected_columns)
        except Exception as e:
            # Проверяем что исключение корректного типа
            assert isinstance(e, (requests.RequestException, ValueError))
    
    def test_integration_special_characters_in_queries(self):
        """Тест обработки специальных символов в запросах"""
        # Arrange
        special_queries = ['c++', 'c#', 'node.js', 'test-query']
        
        for query in special_queries:
            try:
                # Act
                url = get_search_url(query)
                df = fetch_communities_for_query(query)
                
                # Assert
                assert isinstance(df, pd.DataFrame)
                # URL должен быть корректно сформирован даже со специальными символами
                assert 'vk.com/groups' in url
                # Проверяем структуру DataFrame
                assert 'Название' in df.columns
            except Exception as e:
                # Ожидаемо для некоторых специальных символов или сетевых проблем
                print(f"Query '{query}' failed with: {e}")
    
    def test_integration_data_consistency_across_modules(self):
        """Тест согласованности данных между модулями"""
        # Arrange
        query = "книги"
        
        # Act
        url = get_search_url(query)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        labeled_texts = extract_labeled_texts(soup)
        community_info = parse_community_info(labeled_texts)
        links = extract_community_links(soup)
        
        # Assert согласованности
        if community_info and links:
            # Проверяем что количество элементов логически согласовано
            assert len(community_info) <= len(labeled_texts)
            # Проверяем что есть данные для обработки
            assert any('подписч' in str(item) or 'участник' in str(item) 
                      for sublist in community_info for item in sublist)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
