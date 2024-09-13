from collections import Counter, defaultdict
from flask import Flask, render_template, request, redirect, url_for, flash
import io
from pathlib import Path
from pypdf import PdfReader
import re
from werkzeug.utils import secure_filename

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'något vanligt 8'  # Change this to a random string

########################################

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
RIGHT_MARKERS = {
    'Obligatoriska k...':   'Obligatoriska krav',
    'Generell del':         'Generell del',
    '     Information':     'Information',
    'Valfrihet vård- ...':  '',
    'Valfrihet inom ...':   '',
    'Gemensamma...': '',
    }

QUESTION_STARTS_REGEXPS = [re.compile(r'^(\d\.|\d.\d|\d.\d.\d|\d.\d.\d.\d) ')]
QUESTION_ENDS = set(['  Bifogad fil', '  Fritext', '  Ja/Nej.'])


assert QUESTION_STARTS_REGEXPS[0].match('1.5.6 Offentlighetsprincipen/Sekretess')
assert QUESTION_STARTS_REGEXPS[0].match('1.6 Elektronisk avtalssignering')
assert QUESTION_STARTS_REGEXPS[0].match('2. Systematiskt miljöarbete')
assert not QUESTION_STARTS_REGEXPS[0].match('a. Annat')
assert not QUESTION_STARTS_REGEXPS[0].match(' 2. Något')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        # If user does not select file, the browser submits an empty file without a filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Check if the file is allowed (i.e., it's a PDF)
        if not file or not allowed_file(file.filename):
            flash('Allowed file type is PDF')
            return redirect(request.url)

        pdf_filename, pdf_data = write_pdf(file)

        txt_filename = pdf_filename.replace('.pdf', '.txt')
        pdf_to_text(txt_filename, pdf_data)

        return redirect(url_for('upload_file'))

    return render_template('upload.html')


def write_pdf(file):
    filename = secure_filename(file.filename)
    pdf_data = file.read()
    with open(Path(UPLOAD_FOLDER) / filename, 'wb') as local_file:
        local_file.write(pdf_data)
    return filename, pdf_data


def pdf_to_text(txt_filename, pdf_data):
    pdf_file = io.BytesIO(pdf_data)
    pdf_reader = PdfReader(pdf_file)
    pages = []
    metadata = defaultdict(list)
    for page in pdf_reader.pages:
        page_text = page.extract_text(extraction_mode='layout')
        extract_page_meta(page_text, metadata)
        pages.append(page_text)
    metadata = {k:Counter(v) for k,v in metadata.items()}

    lines = cleanup_text_lines(pages, metadata)

    questions = find_questions(lines)
    text = '\n\n'.join(['Question:\n'+q for q in questions])

    with open(Path(UPLOAD_FOLDER) / txt_filename, 'wt', encoding='utf8') as local_file:
        local_file.write(text)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_page_meta(page_text, metadata):
    head = page_text[:4]
    last_line = page_text.rpartition('\n')[2]
    tail = last_line.strip()[:4]
    metadata['head'].append(head)
    metadata['tail'].append(tail)


def cleanup_text_lines(pages, metadata):
    texts = []
    for page_text in pages:
        page_text = cleanup_page(page_text, metadata)
        texts.append(page_text)
    text = '\n'.join(texts)

    lines = text.splitlines()
    lines = cleanup_lines(lines)
    return lines


def find_questions(lines):
    prev_question_end_idx = -1
    for lidx, line in enumerate(lines):
        for qend in QUESTION_ENDS:
            if not line.startswith(qend):
                continue
            question_lines = []
            for i in range(lidx, prev_question_end_idx, -1):
                line = lines[i]
                question_lines.append(line)
                if is_question_start(line):
                    break
            question = '\n'.join(reversed(question_lines))
            yield question.strip()
            prev_question_end_idx = lidx
            break


def cleanup_page(page_text, metadata):
    page_text = page_text.strip()
    if any(page_text.startswith(head) for head, cnt in metadata['head'].items() if cnt>1):
        page_text = page_text.partition('\n')[2]
    prior_text, _, last_line = page_text.rpartition('\n')
    last_line = last_line.strip()
    if any(last_line.startswith(tail) for tail, cnt in metadata['tail'].items() if cnt>1):
        page_text = prior_text
    return page_text.strip()


def cleanup_lines(lines):
    out_lines = []
    for line in lines:
        for mark, out_mark in RIGHT_MARKERS.items():
            i = line.find(mark)
            if i > 0:
                if out_mark:
                    out_lines.append(indent(line) + out_mark)
                line = line[:i] + line[i+len(mark):]
                line = line.rstrip().replace('          ', ' ')
        out_lines.append(line)
    return out_lines


def indent(line):
    return line[:len(line) - len(line.lstrip())]


def is_question_start(line):
    for regexp in QUESTION_STARTS_REGEXPS:
        if regexp.match(line):
            return True
    return False


if __name__ == '__main__':
    app.run(debug=True)
