// netlify/functions/upload.js
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

exports.handler = async function(event, context) {
  const { name, category } = JSON.parse(event.body);

  if (!name || !category) {
    return { statusCode: 400, body: JSON.stringify({ success: false, message: 'Укажите имя и категорию' }) };
  }

  const { error } = await supabase
    .from('files')
    .insert({
      file_name: name,
      category,
      upload_timestamp: new Date().toISOString(),
    });

  if (error) {
    return { statusCode: 500, body: JSON.stringify({ success: false, message: 'Ошибка загрузки' }) };
  }

  return { statusCode: 200, body: JSON.stringify({ success: true, message: 'Файл загружен' }) };
};