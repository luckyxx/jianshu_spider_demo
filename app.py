import re
from lxml import etree

import requests
from fake_useragent import UserAgent
from flask import Flask, request, redirect, url_for, render_template


app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def geturl():
    if request.method== 'POST':
        form_value = request.form['url']
        # match_result = re.match(r'(http://)?(www.jianshu.com/u/)?(.*?)$',form_value)
        match_result = re.match(r'(https://)?(www.jianshu.com/u/)?(\w{12})',form_value)
        if match_result:
            user_slug=match_result.groups()[-1]
            print(user_slug)
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
    slug = request.args.get('slug')
    if slug:
        print('slug：'+slug)
        url='https://www.jianshu.com/u/'+slug
        response=requests.get(url,headers=BASE_HEADERS)
        dom_tree = etree.HTML(response.text)
        main_top=dom_tree.xpath('//div[@class="main-top"]')[0]
        nike_name=dom_tree.xpath('.//a[@class="name"]/text()')[0]
        print(nike_name)
        print(main_top)
        followers=dom_tree.xpath('.//div[@class="meta-block"]/a/p/text()')
        print(followers)
        like_and_font=dom_tree.xpath('.//div[@class="meta-block"]/p/text()')
        print(like_and_font)
        photo = dom_tree.xpath('.//div[@class="main-top"]/a[@class="avatar"]/img/@src')
        print(photo)
        sex_info=dom_tree.xpath('.//div[@class="title"]/i/@class')
        if len(sex_info) ==0:
            sex ='未知'
        else:
            if 'ic-man' in sex_info[0]:
                sex='男'
            elif 'ic-woman' in sex_info[0]:
                sex='女'
        print(sex)
    return render_template('index.html')
if __name__ == '__main__':
    app.run(debug=True)
