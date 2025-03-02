import functools
import html
import os
import re
from transformers import AutoTokenizer
import time
from pathlib import Path

import markdown
from PIL import Image, ImageOps

from modules import shared
from modules.utils import get_available_chat_styles

# This is to store the paths to the thumbnails of the profile pictures
image_cache = {}

with open(Path(__file__).resolve().parent / '../css/html_readable_style.css', 'r') as f:
    readable_css = f.read()
with open(Path(__file__).resolve().parent / '../css/html_instruct_style.css', 'r') as f:
    instruct_css = f.read()

model_id = "nesaorg/Llama-3.1-8B-Instruct-Encrypted"
tokenizer = AutoTokenizer.from_pretrained(model_id)

# Custom chat styles
chat_styles = {}
for k in get_available_chat_styles():
    chat_styles[k] = open(Path(f'css/chat_style-{k}.css'), 'r').read()

# Handle styles that derive from other styles
for k in chat_styles:
    lines = chat_styles[k].split('\n')
    input_string = lines[0]
    match = re.search(r'chat_style-([a-z\-]*)\.css', input_string)

    if match:
        style = match.group(1)
        chat_styles[k] = chat_styles.get(style, '') + '\n\n' + '\n'.join(lines[1:])

def fix_newlines(string):
    string = string.replace('\n', '\n\n')
    string = re.sub(r"\n{3,}", "\n\n", string)
    string = string.strip()
    return string


def replace_quotes(text):

    # Define a list of quote pairs (opening and closing), using HTML entities
    quote_pairs = [
        ('&quot;', '&quot;'),  # Double quotes
        ('&ldquo;', '&rdquo;'),  # Unicode left and right double quotation marks
        ('&lsquo;', '&rsquo;'),  # Unicode left and right single quotation marks
        ('&laquo;', '&raquo;'),  # French quotes
        ('&bdquo;', '&ldquo;'),  # German quotes
        ('&lsquo;', '&rsquo;'),  # Alternative single quotes
        ('&#8220;', '&#8221;'),  # Unicode quotes (numeric entities)
        ('&#x201C;', '&#x201D;'),  # Unicode quotes (hex entities)
    ]

    # Create a regex pattern that matches any of the quote pairs, including newlines
    pattern = '|'.join(f'({re.escape(open_q)})(.*?)({re.escape(close_q)})' for open_q, close_q in quote_pairs)

    # Replace matched patterns with <q> tags, keeping original quotes
    replaced_text = re.sub(pattern, lambda m: f'<q>{m.group(1)}{m.group(2)}{m.group(3)}</q>', text, flags=re.DOTALL)

    return replaced_text


def replace_blockquote(m):
    return m.group().replace('\n', '\n> ').replace('\\begin{blockquote}', '').replace('\\end{blockquote}', '')


@functools.lru_cache(maxsize=None)
def convert_to_markdown(string):

    # Make \[ \]  LaTeX equations inline
    pattern = r'^\s*\\\[\s*\n([\s\S]*?)\n\s*\\\]\s*$'
    replacement = r'\\[ \1 \\]'
    string = re.sub(pattern, replacement, string, flags=re.MULTILINE)

    # Escape backslashes
    string = string.replace('\\', '\\\\')

    # Quote to <q></q>
    string = replace_quotes(string)

    # Blockquote
    string = re.sub(r'(^|[\n])&gt;', r'\1>', string)
    pattern = re.compile(r'\\begin{blockquote}(.*?)\\end{blockquote}', re.DOTALL)
    string = pattern.sub(replace_blockquote, string)

    # Code
    string = string.replace('\\begin{code}', '```')
    string = string.replace('\\end{code}', '```')
    string = string.replace('\\begin{align*}', '$$')
    string = string.replace('\\end{align*}', '$$')
    string = string.replace('\\begin{align}', '$$')
    string = string.replace('\\end{align}', '$$')
    string = string.replace('\\begin{equation}', '$$')
    string = string.replace('\\end{equation}', '$$')
    string = string.replace('\\begin{equation*}', '$$')
    string = string.replace('\\end{equation*}', '$$')
    string = re.sub(r"(.)```", r"\1\n```", string)

    result = ''
    is_code = False
    is_latex = False
    previous_line_empty = True

    for line in string.split('\n'):
        stripped_line = line.strip()

        if stripped_line.startswith('```'):
            is_code = not is_code
        elif stripped_line.startswith('$$'):
            is_latex = not is_latex
        elif stripped_line.endswith('$$'):
            is_latex = False
        elif stripped_line.startswith('\\\\['):
            is_latex = True
        elif stripped_line.startswith('\\\\]'):
            is_latex = False
        elif stripped_line.endswith('\\\\]'):
            is_latex = False

        # Preserve indentation for lists and code blocks
        if stripped_line.startswith('-') or stripped_line.startswith('*') or stripped_line.startswith('+') or stripped_line.startswith('>') or re.match(r'\d+\.', stripped_line):
            result += line + '\n'
            previous_line_empty = False
        elif is_code or is_latex or line.startswith('|'):
            result += line + '\n'
            previous_line_empty = False
        else:
            if previous_line_empty:
                result += line.strip() + '\n'
            else:
                result += line.strip() + '\n\n'

            previous_line_empty = stripped_line == ''

    result = result.strip()
    if is_code:
        result += '\n```'  # Unfinished code block

    # Unfinished list, like "\n1.". A |delete| string is added and then
    # removed to force a <ol> or <ul> to be generated instead of a <p>.
    list_item_pattern = r'(\n\d+\.?|\n\s*[-*+]\s*([*_~]{1,3})?)$'
    if re.search(list_item_pattern, result):
        delete_str = '|delete|'

        if re.search(r'(\d+\.?)$', result) and not result.endswith('.'):
            result += '.'

        # Add the delete string after the list item
        result = re.sub(list_item_pattern, r'\g<1> ' + delete_str, result)

        # Convert to HTML using markdown
        html_output = markdown.markdown(result, extensions=['fenced_code', 'tables'], tab_length=2)

        # Remove the delete string from the HTML output
        pos = html_output.rfind(delete_str)
        if pos > -1:
            html_output = html_output[:pos] + html_output[pos + len(delete_str):]
    else:
        # Convert to HTML using markdown
        html_output = markdown.markdown(result, extensions=['fenced_code', 'tables'], tab_length=2)

    # Unescape code blocks
    pattern = re.compile(r'<code[^>]*>(.*?)</code>', re.DOTALL)
    html_output = pattern.sub(lambda x: html.unescape(x.group()), html_output)

    return html_output


def convert_to_markdown_wrapped(string, use_cache=True):
    '''
    Used to avoid caching convert_to_markdown calls during streaming.
    '''

    if use_cache:
        return convert_to_markdown(string)

    return convert_to_markdown.__wrapped__(string)


def generate_basic_html(string):
    convert_to_markdown.cache_clear()
    string = convert_to_markdown(string)
    string = f'<style>{readable_css}</style><div class="readable-container">{string}</div>'
    return string


def make_thumbnail(image):
    image = image.resize((350, round(image.size[1] / image.size[0] * 350)), Image.Resampling.LANCZOS)
    if image.size[1] > 470:
        image = ImageOps.fit(image, (350, 470), Image.LANCZOS)

    return image


def get_image_cache(path):
    cache_folder = Path(shared.args.disk_cache_dir)
    if not cache_folder.exists():
        cache_folder.mkdir()

    mtime = os.stat(path).st_mtime
    if (path in image_cache and mtime != image_cache[path][0]) or (path not in image_cache):
        img = make_thumbnail(Image.open(path))

        old_p = Path(f'{cache_folder}/{path.name}_cache.png')
        p = Path(f'{cache_folder}/cache_{path.name}.png')
        if old_p.exists():
            old_p.rename(p)

        output_file = p
        img.convert('RGBA').save(output_file, format='PNG')
        image_cache[path] = [mtime, output_file.as_posix()]

    return image_cache[path][1]


def generate_instruct_html(history, tokenize = False):
    output = f'<style>{instruct_css}</style><div class="chat" id="chat"><div class="messages">'
    for i, _row in enumerate(history):
        row = [convert_to_markdown_wrapped(entry, use_cache=i != len(history) - 1) for entry in _row]
        user_input = row[0]
        ai_output = row[1]
        if tokenize:
            user_input = tokenizer.encode(row[0])
            ai_output = tokenizer.encode(row[1])
        if row[0]:  # don't display empty user messages
            output += f"""
                  <div class="user-message">
                    <div class="text">
                      <div class="message-body">
                        {user_input}
                      </div>
                    </div>
                  </div>
                """

        output += f"""
              <div class="assistant-message">
                <div class="text">
                  <div class="message-body">
                    {ai_output}
                  </div>
                </div>
              </div>
            """

    output += "</div></div>"

    return output

def check_file_availability(input_string, substr="[file]"):
    """
    Splits the input string into two parts based on the given substring and removes the substring.
    If the substring appears twice, the second part will contain content between the two occurrences.
    """
    
    pattern = re.escape(substr) + r'(.*?)' + re.escape(substr)
    match = re.search(pattern, input_string)

    if match:
        left_part = input_string[:match.start()].strip()
        middle_part = match.group(1).strip()
        return left_part, middle_part
      
    split_index = input_string.find(substr)
    if split_index != -1:
        left_part = input_string[:split_index].strip()
        right_part = input_string[split_index + len(substr):].strip()
        return left_part, right_part

    return input_string, ""

def generate_cai_chat_html(history, name1, name2, style, character, reset_cache=False,tokenize=False):
    output = f'<style>{chat_styles[style]}</style><div class="chat" id="chat"><div class="messages">'

    # We use ?character and ?time.time() to force the browser to reset caches
    img_bot = '<img src="file/cache/bot.png">'
    img_me = '<img src="file/cache/human-fill.png">'
    img_file = '<img src="file/cache/encryption.png">'
    
    for i, _row in enumerate(history):
        row = [convert_to_markdown_wrapped(entry, use_cache=i != len(history) - 1) for entry in _row]
        row[1], file = check_file_availability(row[1])
        user_input = row[0]
        ai_output = row[1]
        if tokenize:
            user_input = tokenizer.encode(row[0])
            ai_output = tokenizer.encode(row[1])
        
        if row[0]:  # don't display empty user messages
            output += f"""
                  <div class="message">
                    <div class="circle-you">
                      {img_me}
                    </div>
                    <div class="text">
                      <div class="username">
                        {name1}
                      </div>
                      <div class="message-body">
                        {user_input}
                      </div>
                    </div>
                  </div>
                """
        output += f"""
              <div class="message">
                <div class="circle-bot">
                  {img_bot}
                </div>
                <div class="text">
                  <div class="username">
                    {name2}
                  </div>
                  <div class="message-body">
                    {ai_output}
        """
        if file:
            output += f"""
                    <p></p>
                    <a href="https://ipfs-gw-test.nesa.ai/ipfs/{file}" class="file-link" target="_blank">
                      <span class="file-icon">🔗</span>
                      Encryption summary
                    </a>
        """

        output += """
                  </div>
                </div>
              </div>
        """


    return output


def generate_chat_html(history, name1, name2, reset_cache=False, tokenize=False):
    output = f'<style>{chat_styles["wpp"]}</style><div class="chat" id="chat"><div class="messages">'

    for i, _row in enumerate(history):
        row = [convert_to_markdown_wrapped(entry, use_cache=i != len(history) - 1) for entry in _row]
        user_input = row[0]
        ai_output = row[1]
        if tokenize:
            user_input = tokenizer.encode(row[0])
            ai_output = tokenizer.encode(row[1])
        if row[0]:  # don't display empty user messages
            output += f"""
              <div class="message">
                <div class="text-you">
                  <div class="message-body">
                    {user_input}
                  </div>
                </div>
              </div>
            """

        output += f"""
          <div class="message">
            <div class="text-bot">
              <div class="message-body">
                {ai_output}
              </div>
            </div>
          </div>
        """

    output += "</div></div>"
    return output


def chat_html_wrapper(history, name1, name2, mode, style, character, reset_cache=False, tokenize = False):
    if mode == 'instruct':
        return generate_instruct_html(history['visible'])
    elif style == 'wpp':
        return generate_chat_html(history['visible'], name1, name2)
    else:
        return generate_cai_chat_html(history['visible'], name1, name2, style, character, reset_cache, tokenize)
