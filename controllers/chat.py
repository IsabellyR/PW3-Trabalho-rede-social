from flask import request
from flask_socketio import emit

def init_app(socketio):
    @socketio.on("connect")
    def handle_connect():
     print(f"O usuário com a ID: {request.sid} conectou!")
     
     @socketio.on("disconnect")
     def handle_connect():
          print(f"O usuário com a ID: {request.sid} desconectou!")
          
    @socketio.on("join")
    def handle_join(data):
        print(f"{data['nickname']} entrou no chat.")
        emit("join", data, broadcast=True)
        
    @socketio.on("msg")
    def handle_msg(data):
        print(data)
        emit("showmsg", data, broadcast=True)
     
