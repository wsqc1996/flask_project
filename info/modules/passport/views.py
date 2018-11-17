from datetime import datetime
from flask import current_app,session
from flask import make_response
from flask import request, jsonify
import re
from info import constants
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blue
from info import redis_store,db
import random
from info.libs.yuntongxun.sms import CCP
from info.models import User

@passport_blue.route('/image_code')
def generate_image_code():
    """
    从前端接收参数uuid
    参数若不存在返回信息
    调用captcha生成图片验证码
    根据uuid将图片验证码内容存入redis中
    返回图片

    :return:
    """

    image_code_id =  request.args.get('image_code_id')
    print(image_code_id)

    if not image_code_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    name, text, image = captcha.generate_captcha()

    try:
        redis_store.setex('ImageCode_' + image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='存储失败')
    else:
        response = make_response(image)
        response.headers['Content-Type'] = 'image/jpg'
        return response





@passport_blue.route('/sms_code', methods=['POST'])
def send_sms_code():
    """
    从前端接收参数，mobile,image_code,image_code_id
    检查参数是否都在
    检查手机号格式是否正确
    从redis数据库中取出图片验证码
    判断结果是否存在
    删除数据库中图片验证码
    比较图片验证码正确与否
    生成6位随机短信验证码
    把短信验证码存入redis数据库中
    调用CPP发送实现短信
    返回结果


    :return:
    """

    mobile = request.json.get('mobile')
    image_code = request.json.get('image_code')
    image_code_id = request.json.get('image_code_id')

    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')

    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')

    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')

    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码已过期')

    try:
        redis_store.delete('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询失败')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')

    sms_code = ('%06d') % random.randint(0,999999)
    print(sms_code)

    try:
        redis_store.setex('SMSCode_' + mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='存储失败')

    try:
        ccp = CCP()
        result =  ccp.send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='发送短信异常')

    if result == '0':
        return jsonify(errno=RET.OK,errmsg='发送成功')

    else:
        return jsonify(errno=RET.THIRDERR, errmsg='发送失败')






@passport_blue.route('/register',methods=['POST'])
def register():

    """
    本质就是把用户数据存入mysql数据库中
    获取参数，mobile, password，sms_code
    检查参数
    检查手机号格式是否正确
    从redis数据库中获取短信验证码
    如果不存在，短信验证码已过期
    存在就比较短信验证码是否正确
    删除已经比较过的redis数据库中的短信验证码
    正确，就使用模型类对象对密码进行加密存储，传入数据库中
    检查用户是否已经注册，已注册则返回信息,根据手机号
    保存用户信息，如果出错就进行回滚
    保存到缓存当中
    返回结果
    :return:
    """
    mobile = request.json.get('mobile')
    sms_code = request.json.get('sms_code')
    password = request.json.get('password')

    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')

    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    try:
        real_sms_code = redis_store.get('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询失败')

    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码已过期')

    if real_sms_code != str(sms_code):
        return jsonify(errno=RET.DATAERR,errmsg='短信验证码错误')

    try:
        redis_store.delete('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户信息失败')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')

    user = User()
    user.mobile = mobile
    user.password = password
    user.nick_name = mobile

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存用户信息失败')

    session['user_id'] = user.id
    session['mobile'] = mobile
    session['nick_name'] = mobile

    return jsonify(errno=RET.OK, errmsg='注册成功')



@passport_blue.route('/login',methods=['POST'])
def login():
    """
    获取参数
    检查参数完整
    检查手机号格式是否正确
    根据手机号查询用户信息，确认用户是否已注册
    确认密码信息正确
    保存用户登录时间
    保存数据到mysql数据据
    缓存数据

    :return:
    """
    mobile = request.json.get('mobile')
    password = request.json.get('password')

    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')

    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='该用户没有注册')
    if user is None and not user.check_password(password):
        return jsonify(errno=RET.DATAERR,errmsg='用户名或密码错误')

    user.last_login = datetime.now()

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存用户信息失败')

    session['user_id'] = user.id
    session['mobile'] = mobile
    session['nick_name'] = user.nick_name

    return jsonify(errno=RET.OK, errmsg='注册成功')




@passport_blue.route('/logout')
def logout():
    session.pop('user_id',None)
    session.pop('mobile',None)
    session.pop('nick_name',None)

    return jsonify(errno=RET.OK, errmsg='OK')

    pass