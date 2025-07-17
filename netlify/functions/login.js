// netlify/functions/login.js
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

exports.handler = async function(event, context) {
  const { username, password } = JSON.parse(event.body);

  const { data, error } = await supabase
    .from('users')
    .select('password, user_id')
    .eq('username', username)
    .single();

  if (error || !data) {
    return { statusCode: 401, body: JSON.stringify({ success: false }) };
  }

  // Предположим, пароль сохранён в виде хэша в базе
  const isPasswordCorrect = data.password === password;
  if (!isPasswordCorrect) {
    return { statusCode: 401, body: JSON.stringify({ success: false }) };
  }

  const { data: isAdmin } = await supabase
    .from('admin_access')
    .select('status')
    .eq('user_id', data.user_id)
    .maybeSingle();

  return {
    statusCode: 200,
    body: JSON.stringify({
      success: true,
      isAdmin: !!isAdmin,
      username,
    }),
  };
};