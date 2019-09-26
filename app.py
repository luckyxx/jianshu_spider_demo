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


user_timeline ={
    'comment_notes': [],
    'like_notes': [],
    'reward_notes': [],
    'share_notes': [],
    'like_users': [],
    'like_colls': [],
    'like_comments': [],
    'like_notebooks': [],

}
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

def get_mark_time( li):
    '''获取动态产生的时间'''
    mark_time = li.xpath('.//@data-datetime')[0].split('+')[0].replace('T', ' ')
    return mark_time


def get_obj_title( li):
    '''获取文章标题'''
    title = li.xpath('.//a[@class="title"]/text()')[0]
    return title


def get_href_id( li):
    '''获取文章id'''
    href_id = li.xpath('.//a[@class="title"]/@href')[0].split('/')[-1]
    return href_id


def get_comment_text( li):
    '''获取发表评论的内容'''
    like_comment_text = ''.join(li.xpath('.//p[@class="comment"]/text()'))
    return like_comment_text


def get_like_comment_slug( li):
    '''获取赞了用户评论的slug'''
    like_comment_slug = li.xpath('.//div[@class="origin-author single-line"]//@href')[0].split('/')[-1]
    return like_comment_slug


def get_like_comment_note_id( li):
    '''获取评论文章的id'''
    like_comment_note_id = li.xpath('.//div[@class="origin-author single-line"]//@href')[1].split('/')[-1]
    return like_comment_note_id

@app.route('/timeline')
def jianshu_timeline():
    slug=request.args.get('slug')

    if slug:
        print("slug"+slug)
        get_user_info(slug)

        get_user_timeline(slug)
        baseinfo=db['userinfo'].find_one({'nikename':''})
    #     baseinfo={
    #     'nikename':'hahhh'
    # }
        save_timeline_to_mongodb(slug,user_timeline)
        return render_template('index.html',error=slug)
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
    # return item
    return render_template('index.html')


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
    print("tree:"+str(tree))
    print(type(tree))
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
        mark_time = true_dynamic_time.replace('+08:00', '')
        print(data_type, true_dynamic_time)

        if li.xpath('.//span[@data-type="comment_note"]'):
            comment_note = {}
            comment_note['comment_text'] = get_comment_text(li)
            comment_note['time'] = mark_time
            # comment_note['note_title'] = get_obj_title(li)
            comment_note['note_id'] = get_href_id(li)
            print('发表评论', comment_note)
            user_timeline['comment_notes'].append(comment_note)
        elif li.xpath('.//span[@data-type="like_note"]'):
            like_note = {}
            like_note['time'] = mark_time
            # like_note['note_title'] = get_obj_title(li)
            like_note['note_id'] = get_href_id(li)
            print('喜欢文章', like_note)
            user_timeline['like_notes'].append(like_note)
        elif li.xpath('.//span[@data-type="reward_note"]'):
            reward_note = {}
            reward_note['time'] = mark_time
            # reward_note['note_title'] = get_obj_title(li)
            reward_note['note_id'] = get_href_id(li)
            print('赞赏文章', reward_note)
            user_timeline['reward_notes'].append(reward_note)
        elif li.xpath('.//span[@data-type="share_note"]'):
            share_note = {}
            share_note['time'] = mark_time
            # share_note['note_title'] = get_obj_title(li)
            share_note['note_id'] = get_href_id(li)
            print('发表文章', share_note)
            user_timeline['share_notes'].append(share_note)
        elif li.xpath('.//span[@data-type="like_user"]'):
            like_user = {}
            like_user['time'] = mark_time
            like_user['slug'] = get_href_id(li)
            print('关注作者', like_user)
            user_timeline['like_users'].append(like_user)
        elif li.xpath('.//span[@data-type="like_collection"]'):
            like_coll = {}
            like_coll['time'] = mark_time
            like_coll['coll_id'] = get_href_id(li)
            print('关注专题', like_coll)
            user_timeline['like_colls'].append(like_coll)
        elif li.xpath('.//span[@data-type="like_comment"]'):
            like_comment = {}
            like_comment['time'] = mark_time
            like_comment['comment_text'] = get_comment_text(li)
            like_comment['slug'] = get_like_comment_slug(li)
            like_comment['note_id'] = get_like_comment_note_id(li)
            print('赞了评论', like_comment)
            user_timeline['like_comments'].append(like_comment)
        elif li.xpath('.//span[@data-type="like_notebook"]'):
            like_notebook = {}
            like_notebook['time'] = mark_time
            like_notebook['notebook_id'] = get_href_id(li)
            print('关注文集', like_notebook)
            user_timeline['like_notebooks'].append(like_notebook)
        elif li.xpath('.//span[@data-type="join_jianshu"]'):
            join_time = mark_time
            print('加入简书', join_time)
            user_timeline['join_time'] = join_time

    if len(li_tags ) !=0:
        feedid=li_tags[-1].xpath('.//@id')[0]
        maxid=int(feedid[5:]) -1
        print(maxid)
        get_user_timeline(slug,maxid,page+1)


def save_to_mongodb(item):
    db['userinfo'].update({'slug':item['slug']}, {'$setOnInsert':item}, upsert=True)

def save_timeline_to_mongodb(slug,user_timeline):
    all_time=['comment_notes','like_notes','reward_notes','share_notes','like_users','like_colls',
              'like_comments','like_notebooks']
    for tag in all_time:
        if tag in user_timeline:
            db.userinfo.update({'slug':slug},{'$push':{tag:{'$each':user_timeline[tag]}}})  # push 插入字典 each插入列表


if __name__ == '__main__':
    app.run(debug=True)
