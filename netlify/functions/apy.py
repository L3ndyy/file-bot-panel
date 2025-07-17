import json
from flask import Flask, request, jsonify
from supabase import create_client
import os
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Настройка Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    response = supabase.table('users').select('password', 'user_id').eq('username', username).execute()
    if response.data and sha256_crypt.verify(password, response.data[0]['password']):
        is_admin = supabase.table('admin_access').select('status').eq('user_id', response.data[0]['user_id']).execute().data
        return jsonify({'success': True, 'isAdmin': bool(is_admin), 'username': username})
    return jsonify({'success': False, 'message': 'Неверный логин или пароль'}), 401

@app.route('/files', methods=['GET'])
def get_files():
    response = supabase.table('files').select('id', 'file_name', 'category').execute()
    return jsonify(response.data)

@app.route('/upload', methods=['POST'])
def upload_file():
    data = request.get_json()
    file_name = data.get('name')
    category = data.get('category')
    if not file_name or not category:
        return jsonify({'success': False, 'message': 'Укажите название и категорию'}), 400
    response = supabase.table('files').insert({
        'file_name': file_name,
        'category': category,
        'upload_timestamp': '2025-07-17 03:01:00'
    }).execute()
    return jsonify({'success': True, 'message': 'Файл загружен'})

@app.route('/access', methods=['GET'])
def get_access_requests():
    response = supabase.table('access_requests').select('id', 'user_id', 'status').execute()
    return jsonify(response.data)

@app.route('/access/<int:user_id>', methods=['POST'])
def update_access(user_id):
    action = request.get_json().get('action')
    if action == 'approve':
        supabase.table('access_requests').upsert({
            'user_id': user_id,
            'timestamp': '2025-07-17 03:01:00',
            'status': 'approved'
        }).execute()
    elif action == 'revoke':
        supabase.table('access_requests').update({'status': 'revoked'}).eq('user_id', user_id).execute()
    return jsonify({'success': True, 'message': f'Доступ {action} для {user_id}'})

@app.route('/users', methods=['GET'])
def get_users():
    response = supabase.table('users').select('user_id', 'username').execute()
    return jsonify(response.data)

@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    current_user = data.get('currentUser')
    if not username or not password:
        return jsonify({'success': False, 'message': 'Укажите логин и пароль'}), 400
    response = supabase.table('users').select('user_id').eq('username', current_user).execute()
    if not response.data or current_user != 'L3ndy':
        return jsonify({'success': False, 'message': 'Нет прав на добавление пользователей'}), 403
    if supabase.table('users').select('count').eq('username', username).execute().data[0]['count'] > 0:
        return jsonify({'success': False, 'message': 'Пользователь уже существует'}), 400
    new_user_id = supabase.table('users').select('max', 'user_id').execute().data[0]['max'] + 1 or 1
    hashed_password = sha256_crypt.hash(password)
    supabase.table('users').insert({'user_id': new_user_id, 'username': username, 'password': hashed_password}).execute()
    return jsonify({'success': True, 'message': f'Пользователь {username} добавлен'})

@app.route('/users/<string:username>', methods=['PUT'])
def edit_user(username):
    data = request.get_json()
    new_username = data.get('newUsername')
    new_password = data.get('newPassword')
    current_user = data.get('currentUser')
    if not new_username and not new_password:
        return jsonify({'success': False, 'message': 'Укажите новый логин или пароль'}), 400
    response = supabase.table('users').select('user_id').eq('username', current_user).execute()
    if not response.data or current_user != 'L3ndy':
        return jsonify({'success': False, 'message': 'Нет прав на редактирование пользователей'}), 403
    updates = {}
    if new_username and supabase.table('users').select('count').eq('username', new_username).execute().data[0]['count'] == 0:
        updates['username'] = new_username
    if new_password:
        updates['password'] = sha256_crypt.hash(new_password)
    if updates:
        supabase.table('users').update(updates).eq('username', username).execute()
    return jsonify({'success': True, 'message': f'Пользователь {username} обновлён'})

@app.route('/admin/<string:username>', methods=['POST'])
def manage_admin(username):
    data = request.get_json()
    action = data.get('action')
    current_user = data.get('currentUser')
    if not action or action not in ['grant', 'revoke']:
        return jsonify({'success': False, 'message': 'Укажите действие (grant/revoke)'}), 400
    response = supabase.table('users').select('user_id').eq('username', current_user).execute()
    if not response.data or current_user != 'L3ndy':
        return jsonify({'success': False, 'message': 'Нет прав на управление админскими правами'}), 403
    user = supabase.table('users').select('user_id').eq('username', username).execute()
    if not user.data:
        return jsonify({'success': False, 'message': 'Пользователь не найден'}), 404
    user_id = user.data[0]['user_id']
    if action == 'grant':
        supabase.table('admin_access').upsert({'user_id': user_id, 'status': 'approved'}).execute()
    elif action == 'revoke':
        supabase.table('admin_access').delete().eq('user_id', user_id).execute()
    return jsonify({'success': True, 'message': f'Админские права {action} для {username}'})

def handler(event, context):
    with app.test_request_context(
        path=event['path'].replace('/api', ''),  # Удаляем /api для соответствия маршрутам
        method=event['httpMethod'],
        headers=event['headers'],
        body=event['body']
    ):
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': app.dispatch_request().get_data().decode('utf-8')
        }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)