#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : run.py.py
Time    : 2026/3/20 
Author  : xixi
File    : app
#-------------------------------------------------------------
"""
from app import create_app
from app import socketio

app = create_app()

print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
