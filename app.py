import datetime
import re
from collections import Counter

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
    else:
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
        baseinfo=db.userinfo.find_one({'slug':slug})
        if baseinfo:
            pass
        else:
            print("slug"+slug)
            # get_user_info(slug)
            baseinfo = get_user_info(slug)
            get_user_timeline(slug)
            save_timeline_to_mongodb(slug,user_timeline)
            baseinfo['like_notes_num'] = len(user_timeline['like_notes'])
            baseinfo['like_notebooks_num'] = len(user_timeline['like_notebooks'])
            baseinfo['share_notes_num'] = len(user_timeline['share_notes'])
            baseinfo['comment_notes'] = len(user_timeline['comment_notes'])
            baseinfo['reward_notes'] = len(user_timeline['reward_notes'])
            baseinfo['like_comments'] = len(user_timeline['like_comments'])
            baseinfo['update_time']=datetime.datetime.now()
            print(baseinfo['update_time'])

        # baseinfo['share_notes_num'] = len(baseinfo['share_notes'])

        sorted_data = sorted(baseinfo['share_notes'], key=lambda x: x['time'])
        first_share_note=sorted_data[0]

        sorted_data = sorted(baseinfo['like_notes'], key=lambda x: x['time'])
        print("sorted_data:"+str(sorted_data))
        first_like_note = sorted_data[0]

        sorted_data = sorted(baseinfo['like_users'], key=lambda x: x['time'])
        first_like_users = sorted_data[0]

        first_user_dict = {
            'first_like_note': first_like_note,
            'first_like_user': first_like_users,
            'first_share_note':first_share_note,
        }

        zh_parent_tags = ['发表评论', '喜欢文章', '赞赏文章', '发表文章', '关注用户', '关注专题', '点赞评论', '关注文集']
        en_parent_tags = ['comment_notes', 'like_notes', 'reward_notes', 'share_notes',
                          'like_users', 'like_colls', 'like_comments', 'like_notebooks']
        tags_data = []
        index = 0
        for tag in zh_parent_tags:
            dic_tag = {}
            dic_tag['name'] = tag
            dic_tag['value'] = len(baseinfo[en_parent_tags[index]])
            index += 1
            tags_data.append(dic_tag)

        month_lst=[]
        for tag in en_parent_tags:
            for item in baseinfo[tag]:
                month_lst.append(item['time'][0:7])
        # print(month_lst)
        month_counter=Counter(month_lst)
        month_sorted_lst=sorted(month_counter.items(),key=lambda  x:x[0])
        month_frequency_dict={}
        month_frequency_dict['month_line']=[item[0] for item in month_sorted_lst]
        month_frequency_dict['month_freqency']=[item[1] for item in month_sorted_lst]

        day_lst=[]
        for tag in en_parent_tags:
            for item in baseinfo[tag]:
                day_lst.append(item['time'][0:10])
        # print(day_lst)
        day_counter = Counter(day_lst)
        day_sorted_lst = sorted(day_counter.items(), key=lambda x: x[0])
        # print(day_sorted_lst)
        day_frequency_dict = {}
        day_frequency_dict['day_line'] = [item[0] for item in day_sorted_lst]
        day_frequency_dict['day_freqency'] = [item[1] for item in day_sorted_lst]

        hour_lst = []
        for tag in en_parent_tags:
            for item in baseinfo[tag]:
                hour_lst.append(item['time'][12:16])
        # print(hour_lst)
        hour_counter = Counter(hour_lst)
        hour_sorted_lst = sorted(hour_counter.items(), key=lambda x: x[0])
        # print(day_sorted_lst)
        hour_frequency_dict = {}
        hour_frequency_dict['hour_line'] = [item[0] for item in hour_sorted_lst]
        hour_frequency_dict['hour_freqency'] = [item[1] for item in hour_sorted_lst]

        time_lst=[]
        for tag in en_parent_tags:
            for item in baseinfo[tag]:
                time_lst.append(item['time'][0:])
        print(time_lst)
        # for x in time_lst:
        user_week_you_want=[day_to_week(x) for x in time_lst]
        # print(user_week_you_want)
        counter_you_want_f = Counter(user_week_you_want)
        sort_counter = sorted(counter_you_want_f.items(), key=lambda t: t[0])
        # print(sort_counter)
        week_data={}
        week_data['week_line']=[ item[0] for item in sort_counter]
        week_data['week_freqency']=[item[1] for item in sort_counter]




        ###气泡图数据
        week_hour_lst = []
        for item in baseinfo['share_notes']:
            week = date_to_week(item['time'])  # 周日----6
            hour = item['time'][12:14]  # '2019-09-08 11:32:15'
            week_hour = str(week) + hour  # 611
            week_hour_lst.append(week_hour)

        counter_week_hour = Counter(week_hour_lst)
        max_freq = counter_week_hour.most_common(1)[0][1]

        # ('611',5)-->#[6,11,5]
        result_lst = []
        for item in counter_week_hour.items():
            lst_item = [int(item[0][0]), int(item[0][1:3]), item[1]]
            result_lst.append(lst_item)
        return render_template('timeline.html',
                               baseinfo=baseinfo,
                               first_user_dict=first_user_dict,
                               tags_data=tags_data,
                               month_data=month_frequency_dict,
                               day_data=day_frequency_dict,
                               hour_data=hour_frequency_dict,
                               week_data=week_data,
                               week_hour_share_notes=result_lst,
                               max_freq=max_freq)
    else:
        return render_template('index.html')

def date_to_week(time_str):
    timeobj = datetime.datetime.strptime(time_str,'%Y-%m-%d %H:%M:%S')
    week = timeobj.weekday()
    return week

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
    item['photo'] = dom_tree.xpath('.//div[@class="main-top"]/a[@class="avatar"]/img/@src')[0]
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
    return item


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
            comment_note['comment_text'] = get_comment_text(li).replace('\n','').strip()
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

def day_to_week(day_string):
    time = datetime.datetime.strptime(day_string, '%Y-%m-%d %H:%M:%S')
    week_day = time.weekday()
    week_day_dict = {0: '周一', 1: '周二', 2: '周三', 3: '周四',
                     4: '周五', 5: '周六', 6: '周日', }
    return week_day_dict[week_day]

if __name__ == '__main__':
    app.run(debug=True)
