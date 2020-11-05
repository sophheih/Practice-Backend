from datetime import datetime, timedelta
from django.utils.timezone import now

import jwt
import mongoengine

from config import config


class Member(mongoengine.Document):
    username = mongoengine.StringField()
    real_name = mongoengine.StringField()
    password_md5 = mongoengine.StringField()
    balance = mongoengine.IntField(default=0)
    gender = mongoengine.StringField(choices=('男', '女'))
    cellphone = mongoengine.StringField()
    email = mongoengine.StringField()

    @property
    def token(self):
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        token = jwt.encode({
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'data': {
                'id': str(self.id),
                'admin': False
            }
        }, config['SECRET_KEY'], algorithm='HS256')

        return token.decode('utf-8')



class Service(mongoengine.Document):
    title = mongoengine.StringField()
    short_description = mongoengine.StringField()
    long_description = mongoengine.StringField()
    duration = mongoengine.IntField()
    price = mongoengine.IntField()


class Reservation(mongoengine.Document):
    member_id = mongoengine.ObjectIdField()
    total_price = mongoengine.IntField()
    start_time = mongoengine.DateTimeField()
    end_time = mongoengine.DateTimeField()
    services = mongoengine.ListField()


class Order(mongoengine.Document):
    create_time = mongoengine.DateTimeField(required=True)
    ip = mongoengine.StringField(required=True)
    amount = mongoengine.IntField(required=True)
    member_id = mongoengine.ObjectIdField(required=True)
    status = mongoengine.StringField(required=True)
    payment_time = mongoengine.DateTimeField(required=False)
    error_msg = mongoengine.StringField(required=False)

class Timetable(mongoengine.Document):
    date = mongoengine.IntField()
    time = mongoengine.DictField(default={})

