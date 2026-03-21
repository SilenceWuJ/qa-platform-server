#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : config.py
Time    : 2026/3/20 
Author  : xixi
File    : app/conf
#-------------------------------------------------------------
"""
import os

# class Config:
#     SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
#     SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///qa_platform.db'
#     SQLALCHEMY_TRACK_MODIFICATIONS = False


import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    # MySQL 配置
    DB_USER = 'qa_user'  # 替换为实际用户名
    DB_PASSWORD = '123456'  # 替换为实际密码
    DB_HOST = 'localhost'  # 或 IP 地址
    DB_PORT = '3306'
    DB_NAME = 'qa_platform'

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
