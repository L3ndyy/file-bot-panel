// netlify/functions/users.js
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

exports.handler = async function(event, context) {
  const method = event.httpMethod;

  if (method === 'GET') {
    const { data, error } = await supabase.from('users').select('user_id, username');
    if (error) return { statusCode: 500, body: JSON.stringify({ success: false }) };
    return { statusCode: 200, body: JSON.stringify(data) };
  }

  if (method === 'POST') {
    const { username, password, currentUser } = JSON.parse(event.body);

    if (!username || !password) {
      return { statusCode: 400, body: JSON.stringify({ success: false, message: 'Укажите логин и пароль' }) };
    }

    if (currentUser !== 'L3ndy') {
      return { statusCode: 403, body: JSON.stringify({ success: false, message: 'Нет прав' }) };
    }

    const { data: existingUser } = await supabase
      .from('users')
      .select('count')
      .eq('username', username)
      .single();

    if (existingUser.count > 0) {
      return { statusCode: 400, body: JSON.stringify({ success: false, message: 'Пользователь существует' }) };
    }

    const { data: maxId } = await supabase.from('users').select('max(user_id)').single();
    const newUser = {
      user_id: maxId.max + 1,
      username,
      password,
    };

    const { error } = await supabase.from('users').insert(newUser);
    if (error) return { statusCode: 500, body: JSON.stringify({ success: false, message: 'Ошибка добавления' }) };

    return { statusCode: 200, body: JSON.stringify({ success: true, message: `Пользователь ${username} добавлен` }) };
  }

  return { statusCode: 405, body: 'Method not allowed' };
};