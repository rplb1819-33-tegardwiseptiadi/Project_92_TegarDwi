import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask import (
    Flask, 
    request,
    render_template,
    redirect,
    url_for,
    jsonify 
)

from pymongo import MongoClient
import requests
from bson import ObjectId
from datetime import datetime

# tegar dwi septiadi

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)

@app.route('/')
def main():
    # This route should fetch all of 
    # the words from the database and 
    # pass them on to the HTML template
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template(
        'index.html',
        words=words,
        msg=msg
    )

@app.route('/error_page/<keyword>')
def error_page(keyword):
    error_message = f'Could not find the word "{keyword}"'
    api_key = '9b7ba837-91ca-4a04-bab7-eb5cad0b5a16'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()

    suggestions = []  # Inisialisasi list untuk menyimpan saran

    if not definitions:  # Jika tidak ada definisi yang ditemukan
        return redirect(url_for('error', keyword=keyword, suggestions=suggestions, error_message=error_message))

    if type(definitions[0]) is str:  # Jika definisi adalah string tunggal
        # Mengambil saran dari definisi yang diberikan
        for defn in definitions:
            if defn != keyword:
                suggestions.append(defn)
        return redirect(url_for('error', keyword=keyword, suggestions=suggestions, error_message=error_message))

    return render_template('error.html', error_message=error_message, suggestions=suggestions)

@app.route('/error')
def error():
    error_message = request.args.get('error_message')
    keyword = request.args.get('keyword')
    suggestions = request.args.getlist('suggestions')  # Menggunakan 'suggestions' di sini
    return render_template('error.html', error_message=error_message, keyword=keyword, suggestions=suggestions)


@app.route('/detail/<keyword>')
def detail(keyword):
    # This handler should find the requested word through the dictionary API and pass the data for that word onto the template
    
    api_key = '9b7ba837-91ca-4a04-bab7-eb5cad0b5a16'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()


    status = request.args.get('status_give', 'new')
    return render_template(
        'detail.html',
        word=keyword,
        definitions=definitions,
        status=status
    )


@app.route('/api/save_word', methods=['POST'])
def save_word():
    #  This handler should save the word in the database
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y%m%d'),
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })


@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    #  This handler should delete the word from the database
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was deleted'
    })

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word') 
    example_data = db.examples.find({'word': word}) 
    examples = []
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id')),
        })
    return jsonify({
        'result': 'success',
        'examples':examples
        })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word') 
    example = request.form.get('example') 
    doc = {
        'word':word,
        'example':example,
    }
    db.examples.insert_one(doc)
    return jsonify({
        'result': 'success', 
        'msg': f'Your example, {example}, for the word, {word} was saved!',
        })


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id':ObjectId(id)})
    
    return jsonify({
        'result': 'success',
        'msg': f'Your example for the word, {word}, was deleted!',
        })

# @app.route('/practice')
# def practice(): 
#     return render_template('practice.html')
 
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)