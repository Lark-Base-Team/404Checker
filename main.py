import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from check_job import check_job
from exceptions import FieldError, PersonalBaseTokenError


# 临时测试mysql数据库，需修改！
data_base_config={
    "username":"", # 用户名
    "password":"", # 密码
    "ip":"", # ip
    "port":"3306", # port
    "databaseName":"task" # 数据库名
}
# 定时任务调度器配置
scheduler = BackgroundScheduler({
    'apscheduler.jobstores.default': {
        'type': 'sqlalchemy',
        'url': 'mysql+pymysql://' + data_base_config['username'] + ':' + data_base_config['password'] + '@' +
               data_base_config['ip'] + ':' + data_base_config['port'] + '/' + data_base_config[
                   'databaseName'] + '?charset=utf8',
        'tablename': 'check_job'
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': '20'
    },
    'apscheduler.executors.processpool': {
        'type': 'processpool',
        'max_workers': '10'
    },
    'apscheduler.job_defaults.coalesce': 'true',
    'apscheduler.job_defaults.max_instances': '20',
    'apscheduler.timezone': 'Asia/Shanghai',
})

app = Flask(__name__, template_folder="./dist", static_folder="./dist/assets")
CORS(app, supports_credentials=True)


@app.route('/getTask', methods=["POST"])
def getTask():
    # 获取参数
    tableId = request.json.get('tableId')

    job = scheduler.get_job(tableId)
    if job==None:
        return {"code": 400, "msg": "任务不存在", "data": {}}
    return {"code": 200, "msg": "获取成功", "data": {"next_run_time": job.next_run_time, "id": job.id}}

@app.route('/deleteTask', methods=["POST"])
def deleteTask():
    # 获取参数
    try:
        tableId = request.json.get('tableId')
        scheduler.remove_job(tableId)
    except:
        return {"code": 400, "msg": "删除失败", "data": {}}

    return {"code": 200, "msg": "删除失败", "data": {}}

@app.route('/startTask', methods=["POST"])
def startTask():
    '''
    启动任务
    :return:
    '''
    # 获取参数
    baseId = request.json.get('baseId')
    tableId = request.json.get('tableId')
    personalBaseToken = request.json.get('personalBaseToken')
    fieldToCheck = request.json.get('fieldToCheck')
    checkFreq = request.json.get('checkFreq')
    # 参数校验
    if baseId == '' or tableId == '' or personalBaseToken == '' or fieldToCheck == '' or checkFreq == '':
        return {'code': 400, 'msg': '请完整填写表单参数'}
    try:
        # 进行一次检查任务
        check_job(baseId, tableId, personalBaseToken, fieldToCheck)
        # 添加定时任务
        scheduler.add_job(func=check_job, replace_existing=True, trigger='interval', seconds=checkFreq,
                          id=tableId,
                          args=[baseId, tableId, personalBaseToken, fieldToCheck])
    # 异常处理
    except FieldError as e:
        return {'code': 400, 'msg': e.msg}
    except PersonalBaseTokenError as e:
        return {'code': 400, 'msg': e.msg}
    except Exception as e:
        print(e)
        return {'code': 400, 'msg': '未知异常，任务添加失败'}
    # 返回结果
    return {'code': 200, 'msg': '任务添加成功'}

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    scheduler.start()
    app.run(host='0.0.0.0',debug=True)
