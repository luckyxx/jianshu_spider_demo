import re

import pymongo
from lxml import etree

import requests
from fake_useragent import UserAgent
from flask import Flask, request, redirect, url_for, render_template

app = Flask(__name__)
MONGO_HOST = 'localhost'
MONGO_DATABASE = 'JianShu'

client = pymongo.MongoClient(MONGO_HOST)
db = client[MONGO_DATABASE]

@app.route('/', methods=['POST', 'GET'])
def geturl():
    if request.method== 'POST':
        form_value = request.form['url']
        # match_result = re.match(r'(http://)?(www.jianshu.com/u/)?(.*?)$',form_value)
        match_result = re.match(r'(https://)?(www.jianshu.com/u/)?(\w{12})',form_value)
        if match_result:
            user_slug=match_result.groups()[-1]
            # print(user_slug)
            return redirect(url_for('jianshu_timeline',slug=user_slug))
        else:
            return render_template('index.html',error_msg='输入的用户主页有问题！请重新输入！')
    return render_template('index.html')

BASE_HEADERS = {
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
    'Host': 'www.jianshu.com',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': 'text/html, */*; q=0.01',
    'User-Agent': UserAgent().random,
    'Connection': 'keep-alive',
    'Referer': 'http://www.jianshu.com',
}

@app.route('/timeline')
def jianshu_timeline():
    slug=request.args.get('slug')
    if slug:
        print("slug"+slug)
        get_user_info(slug)

        get_user_timeline(slug)
        return render_template('index.html',error_msg=slug)
    else:
        return render_template('index.html')



def get_user_info(slug):
    url = 'https://www.jianshu.com/u/' + slug
    response = requests.get(url, headers=BASE_HEADERS)
    dom_tree = etree.HTML(response.text)
    item = {}
    main_top = dom_tree.xpath('//div[@class="main-top"]')[0]
    item['slug'] = slug
    item['nike_name'] = main_top.xpath('.//a[@class="name"]/text()')[0]
    # print(nike_name)
    # print(main_top)
    base_infos = dom_tree.xpath('.//li//p/text()')
    # print(followers)
    item['following'] = base_infos[0]
    item['follower'] = base_infos[1]
    item['article_nums'] = base_infos[2]
    item['words_num'] = base_infos[3]
    item['like_nums'] = base_infos[4]
    item['photo'] = dom_tree.xpath('.//div[@class="main-top"]/a[@class="avatar"]/img/@src')
    # print(photo)
    sex_info = dom_tree.xpath('.//div[@class="title"]/i/@class')
    if len(sex_info) == 0:
        sex = '未知'
    else:
        if 'ic-man' in sex_info[0]:
            sex = '男'
        elif 'ic-woman' in sex_info[0]:
            sex = '女'
    # print(sex)
    item['sex'] = sex
    save_to_mongodb(item)
    # return render_template('timeline.html')


def get_user_timeline(slug,maxid=-1,page=1):
    #  爬取简述用户的动态信息
    url=''
    if maxid==-1:
        url=f'https://www.jianshu.com/users/{slug}/timeline'
    else:
        url=f'https://www.jianshu.com/users/{slug}/timeline?max_id={maxid}&page={page}'
    # print('url:'+url)
    response = requests.get(url,headers=BASE_HEADERS)
    tree = etree.HTML(response.text)
    # print("tree:"+str(tree))
    # print(type(tree))
    li_tags = tree.xpath('//ul[@class="note-list"]/li')
    # print(li_tags)
    response = requests.get(url, headers=BASE_HEADERS)
    tree = etree.HTML(response.text)
    li_tags = tree.xpath('//ul[@class="note-list"]/li')
    # class ="note-list"] // li / text()
    # print(li_tags)

    for li in li_tags:
        data_type = li.xpath('.//div[@class="info"]/span/@data-type')[0]
        dynamic_time = li.xpath('.//div[@class="info"]/span/@data-datetime')
        true_dynamic_time = dynamic_time[0].replace('T', '  ')
        true_dynamic_time = true_dynamic_time.replace('+08:00', '')
        print(data_type, true_dynamic_time)

    if len(li_tags ) !=0:
        feedid=li_tags[-1].xpath('.//@id')[0]
        maxid=int(feedid[5:]) -1
        print(maxid)
        get_user_timeline(slug,maxid,page+1)


def save_to_mongodb(item):
    db['userinfo'].update({'slug':item['slug']}, {'$setOnInsert':item}, upsert=True)

if __name__ == '__main__':
    app.run(debug=True)
