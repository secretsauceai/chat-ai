from flask import Flask, request, jsonify
from transformers import pipeline
import sqlite3
import toml
import os

app = Flask(__name__)
conn = sqlite3.connect('../responses.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS responses (id INTEGER PRIMARY KEY AUTOINCREMENT, input_prompt TEXT, generated_text TEXT, model TEXT, preprompt TEXT DEFAULT NULL, vote INTEGER DEFAULT NULL)')
conn.commit()
c.close()
conn.close()

# Check if there are any environment variables set, if not, load from config.toml:
try:
    CHECKPOINT = os.environ['CHECKPOINT']
    PORT = os.environ['PORT']
    PREPROMPT = os.environ['PREPROMPT']


    config = {'checkpoint': CHECKPOINT, 'preprompt': PREPROMPT, 'port': PORT}

except:
    config = toml.load('../config/config.toml')

if 't5' in config['checkpoint'].lower() or 'flan' in config['checkpoint'].lower():
    model = pipeline('text2text-generation', model=config['checkpoint'], use_fast=True, truncation=False)
    print('Using T5 model')

else:
    model = pipeline('text-generation', model=config['checkpoint'], use_fast=True)
    print('Using GPT model')

def query_db(query, data): 
    # Create a new database connection and cursor object
    conn = sqlite3.connect('../responses.db')
    c = conn.cursor()

    # Insert the response into the database
    result = c.execute(query, data)

    # Commit the changes and close the connection and cursor
    conn.commit()
    c.close()
    conn.close()
    return result

@app.route('/generate_text', methods=['POST'])
def generate_text():
    if 't5' in config['checkpoint'].lower() or 'flan' in config['checkpoint'].lower():
        input_prompt = request.json['input_prompt']
        #instruction = request.json['input_prompt']
        #input_prompt = f"Below is an instruction that describes a task. Write a response that appropriately completes the request. \n\n### Instruction:\n{instruction}\n\n### Response:\n"
        instruction = None
    else:
        instruction = request.json['input_prompt']
        preprompt = config['preprompt']
        input_prompt = preprompt.replace('{instruction}', instruction)
        #input_prompt = f"Below is an instruction that describes a task. Write a response that appropriately completes the request. \n\n### Instruction:\n{instruction}\n\n### Response:\n"
    generated_text = model(input_prompt, max_length=768, do_sample=False)[0]['generated_text']
    if input_prompt in generated_text:
        generated_text = generated_text.replace(input_prompt, '')

    if instruction:
        input_prompt = instruction
    else:
        preprompt = None

    response = query_db('INSERT INTO responses (input_prompt, generated_text, model, preprompt) VALUES (?, ?, ?, ?)', (input_prompt, generated_text, config['checkpoint'], preprompt))

    json_response = jsonify(
        {
            'generated_text': generated_text,
            'response_id': response.lastrowid,
            'input_prompt': input_prompt,
            'model': config['checkpoint']
            }
         )

    return json_response

@app.route('/vote', methods=['POST'])
def vote(): 
    vote_value = request.json['vote']
    response_id = request.json['response_id'] 
    query_db('UPDATE responses SET vote = ? WHERE id = ?', (vote_value, response_id))

    return jsonify({
        'success': True,
    })

if __name__ == '__main__':
    app.run(debug=True, port=config['port'], host='0.0.0.0')

#TODO: add user id from telegram to DB