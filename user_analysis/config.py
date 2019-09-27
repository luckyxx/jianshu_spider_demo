import datetime

USER = 'default'
START_TIME = 'register_time'
END_TIME='yesterday'
TIMELINE_TYPES=('comment_nots','like_notes','reward_notds','share_nots',
               'like_users','like_colls','like_comments','like_notbooks')

MONGO_HOST='localhost'
MONGO_PORT=27017
MONGO_TABLE='JianShu'

UPDATE=True

# def day_to_week():
#     day_string=str('2019-09-27 11:12:27')
#     time = datetime.datetime.strptime(day_string, '%Y-%m-%d %H:%M:%S')
#     week_day = time.weekday()
#     week_day_dict = {0: '周一', 1: '周二', 2: '周三', 3: '周四',
#                      4: '周五', 5: '周六', 6: '周日', }
#     return week_day_dict[week_day]
# if __name__ == '__main__':
#     print(day_to_week())

