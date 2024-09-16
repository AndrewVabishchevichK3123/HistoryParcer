from bs4 import BeautifulSoup  #все четыре библиотеки необходимо установить
import requests
import pandas as pd

url1 = 'https://vk.com/groups?act=catalog&c%5Blike_hints%5D=1&c%5Bper_page%5D=40&c%5Bq%5D='
url2 = '&c%5Bsection%5D=communities'
peoples = ['abazin', 'бесермяне', 'нагайбаки', 'удэгейцы', 'ульчи', 'чулымцы', 'шапсуги', 'эскимосы', 'юкагиры',
           'ительмены', 'камчадалы', 'долганы', 'кереки']  #сюда записываем народы наши великие

path=input("Укажите путь, куда сохранится таблица excel " + '\n'
           "(пример записи - C:/Users/andry/Downloads/parcer.xlsx, где parcer.xlsx - таблица с будущими данными); учтите слеш: ")

total = {}
ds = []
for people in peoples:

    url3 = people
    url = url1 + url3 + url2

    response = requests.get(url)
    bs = BeautifulSoup(response.text, "html.parser")

    all = bs.findAll('div', 'labeled')
    # print(all)
    nums = list('0123456789')
    for i in range(len(all)):
        all[i] = all[i].text

    info = []
    group = []
    i = 0
    while True:

        c = all[i]
        if c != '':
            group.append(c)
            if c == ' \n\nГосорганизация':
                group[-1] = 'Госорганизация'

            if len(group)==3 and 'подписч' not in c and 'участник' not in c:
                group[-2] = group[-2]+', '+group[-1]
                group.pop(-1)

            if 'подписч' in c or 'участник' in c:
                info.append(group)
                group = []

        i += 1
        if i == len(all):
            break

    all = bs.findAll('a', href=True)
    id = []
    stop = ['', 'games', '/', '/video', '', '/join', '/restore', '/audio', 'video', '/groups/recommendations', 'services',
            'apps', '/mobile?utm_source=menu', '/legal/recommendations', '/groups?act=catalog',
            '/groups?act=catalog&c[category]=0', '/groups?act=catalog&c[category]=1',
            '/groups?act=catalog&c[category]=2', '/groups?act=catalog&c[category]=3',
            '/groups?act=catalog&c[category]=5', '/groups?act=catalog&c[category]=9',
            '/groups?act=catalog&c[category]=4', '/groups?act=catalog&c[category]=10',
            '/groups?act=catalog&c[category]=7', '/groups?act=catalog&c[category]=12',
            '/groups?act=catalog&c[category]=8', '/groups?act=catalog&c[category]=15',
            '/groups?act=catalog&c[category]=6', '/groups?act=catalog&c[category]=11',
            '/groups?act=catalog&c[category]=17', '/groups?act=catalog&c[category]=18',
            '/groups?act=catalog&c[category]=19', '/groups?act=catalog&c[category]=20',
            '/groups?act=catalog&c[category]=21', '/groups?act=catalog&c[category]=22',
            '/groups?act=catalog&c[category]=23', '/groups?act=catalog&c[category]=24',
            '/groups?act=catalog&c[category]=32', '/groups?act=catalog&c[category]=25',
            '/groups?act=catalog&c[category]=26', '/groups?act=catalog&c[category]=31', '/about', '/about',
            '/support?act=home', '/terms', '/biz?utm_source=vk_inside&utm_medium=authorization', 'https://dev.vk.com',
            '/jobs', '/verify', '/services', '/games']

    for el in all:
        if el['href'] not in stop:
            id.append('https://vk.com' + el['href'])
    id = id[::2]
    for t in range(len(info)):
        info[t].append(id[t])
        if len(info[t]) == 3:
            info[t].insert(1, '-')
        info[t].insert(0, str(t + 1))

    exc = {'№': [], 'Название': [], 'Тип сообщества': [], 'Численность': [], 'Ссылка': []}
    for i in range(len(info)):
        exc['№'].append(info[i][0])
        exc['Название'].append(info[i][1])
        exc['Тип сообщества'].append(info[i][2])
        exc['Численность'].append(info[i][3])
        exc['Ссылка'].append(info[i][4])
    ds.append(pd.DataFrame(exc))
total = dict(zip(peoples, ds))
writer = pd.ExcelWriter(path, engine='xlsxwriter')
for sheet_name in total.keys():
    total[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)
writer.close()
