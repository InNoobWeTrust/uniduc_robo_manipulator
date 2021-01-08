import hashlib
from datetime import datetime

from flask import current_app, request, url_for
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class RoboticPermission:
    VIEW = 0x01
    CONTROL = 0x02
    MANAGE = 0x04
    ADMINISTER = 0x80


class RoboticRole(db.Model):
    __tablename__ = 'robotic_roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    @staticmethod
    def insert_roles():
        roles = {
            'Operator':
            (RoboticPermission.VIEW | RoboticPermission.CONTROL, True),
            'Manager':
            (RoboticPermission.VIEW | RoboticPermission.MANAGE, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = RoboticRole.query.filter_by(name=r).first()
            if role is None:
                role = RoboticRole(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Robotic Role %r>' % self.name


class Robot(db.Model):
    __tablename__ = 'robots'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    serial = db.Column(db.String(256), unique=True, index=True)
    user_relations = db.relationship('RobotUser',
                                     backref='robot',
                                     lazy='dynamic')

    @staticmethod
    def generate_fake():
        import forgery_py
        dummy_robot = Robot(name=forgery_py.name.full_name(), serial='dummy')
        db.session.add(dummy_robot)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


class RobotUser(db.Model):
    __tablename__ = 'robot_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    robot_id = db.Column(db.Integer, db.ForeignKey('robots.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('robotic_roles.id'))
    __table_args__ = (UniqueConstraint('user_id',
                                       'robot_id',
                                       name='_robot_user_uc'), )

    @staticmethod
    def generate_fake():
        user = User.query.filter_by(username='admin').first()
        robot = Robot.query.filter_by(serial='dummy').first()
        role = RoboticRole.query.filter_by(name='Administrator').first()
        robot_user = RobotUser(user_id=user.id,
                               robot_id=robot.id,
                               role_id=role.id)
        db.session.add(robot_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


class User(UserMixin, db.Model):
    """
    TODO: implement relationship with robots
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    avatar_hash = db.Column(db.String(32))
    robot_relations = db.relationship('RobotUser',
                                      backref='user',
                                      lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from random import seed

        import forgery_py
        from sqlalchemy.exc import IntegrityError

        seed()
        for i in range(count):
            u = User(
                email=forgery_py.internet.email_address()
                if i != 0 else 'admin@example.com',
                username=forgery_py.internet.user_name(True)
                if i != 0 else 'admin',
                password=forgery_py.lorem_ipsum.word() if i != 0 else 'admin',
                confirmed=True,
                name=forgery_py.name.full_name(),
            )
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return f'{url}/{hash}?s={size}&d={default}&r={rating}'

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def __repr__(self):
        return '<User %r>' % self.username
