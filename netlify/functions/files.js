// netlify/functions/files.js
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

exports.handler = async function(event, context) {
  const { data, error } = await supabase
    .from('files')
    .select('id, file_name, category');

  if (error) {
    return { statusCode: 500, body: JSON.stringify({ success: false }) };
  }

  return { statusCode: 200, body: JSON.stringify(data) };
};