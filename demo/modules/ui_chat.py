import json
from functools import partial
from pathlib import Path

import gradio as gr
from PIL import Image

from modules import chat, shared, ui, utils
from modules.html_generator import chat_html_wrapper
from modules.text_generation import stop_everything_event
from modules.utils import gradio
import base64
inputs = ('Chat input', 'interface_state')
reload_arr = ('history', 'name1', 'name2', 'mode', 'chat_style', 'character_menu')

custom_css = """
#sampling-parameters-heading, #model-settings-heading {
    margin-bottom: 5px; /* Close the gap between heading and line */
    margin-top: 5px;
    padding: 0;
    text-align: center; /* Center-align the headings */
    font-size: var(--text-lg);
    font-weight: var(--prose-header-text-weight);
    line-height: 1.3;
    color: var(--body-text-color);
}
#model-settings-heading {
    margin-top: 3px;
}
#sampling-parameters-divider, #model-settings-divider {
    border: 0;
    border-top: 1px solid #555; /* Dimmer line color */
    margin: 0; /* Remove margin to stick it close to the heading */
    width: 100%; /* Full-width underline */
    margin-bottom: 5px !important;
}
#left-chat{
    padding: 0 10px;
}
[id$="-slider"] input[type=range].svelte-pc1gm4 {
    background-image: linear-gradient(#3669d6, #3669d6) !important;
}

"""
def create_ui():

    mu = shared.args.multi_user
    shared.gradio['Chat input'] = gr.State()
    shared.gradio['tokenize'] = gr.State(False)
    shared.gradio['history'] = gr.JSON({'internal': [], 'visible': []}, visible=False)
    custom_html = """
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
        """
    with gr.Row():
        gr.HTML(value=custom_html)
        gr.HTML(value="""<div id = "output-text" class = "output-text">output</div>""")
        shared.gradio['Output Off'] = gr.Button(value="", elem_id="toggle-off", elem_classes="toggle")
        shared.gradio['Output On'] = gr.Button(value="", elem_id="toggle-on", elem_classes="toggle hideCurOutput")
    with gr.Tab('Chat', elem_id='chat-tab',visible=True):
        with gr.Row(elem_id='past-chats-row', elem_classes=['pretty_scrollbar']):
            with gr.Column(elem_id=['left-chat']):
                with gr.Row():
                    shared.gradio['unique_id'] = gr.Radio(label="", elem_classes=['slim-dropdown', 'pretty_scrollbar'], interactive=not mu, elem_id='past-chats')


                with gr.Row(elem_id='rename-row', visible=False) as shared.gradio['rename-row']:
                    shared.gradio['rename_to'] = gr.Textbox(label='Rename to:', placeholder='New name', elem_classes=['no-background'])

                gr.HTML(f"<style>{custom_css}</style>")

                # Model Settings Section Heading
                gr.HTML(
                    value='<div id="model-settings-container">'
                          '<div id="model-settings-heading">Model Settings</div>'
                          '<hr id="model-settings-divider">'
                          '</div>'
                )
                gr.Dropdown(
                label="Model",
                choices=['Llama-3.1-8B-Instruct-ee'],
                value='Llama-3.1-8B-Instruct-ee',
                elem_id="model-dropdown",
                interactive=True)
                gr.Dropdown(
                label="Response Format",
                choices=["text"],  # Add more formats if available
                value="text",
                elem_id="response-format-dropdown",
                interactive=True)
                gr.HTML(
                    value='<div id="sampling-parameters-container">'
                          '<div id="sampling-parameters-heading">Sampling Parameters</div>'
                          '<hr id="sampling-parameters-divider" style="margin: 0;">'
                          '</div>'
                )
                shared.gradio['temperature'] = gr.Slider(
                    label="Temperature",
                    minimum=0.0,
                    maximum=2.0,
                    value=1.0,
                    step=0.01,
                    elem_id="temperature-slider",
                    interactive=True
                )
                shared.gradio['max_new_tokens'] = gr.Slider(
                label="Max Tokens",
                minimum=1,
                maximum=4096,  # Adjust the max value based on your model
                value=2048,
                step=1,
                elem_id="max-tokens-slider",
                interactive=True)
                shared.gradio['top_p'] = gr.Slider(
                label="Top P",
                minimum=0.0,
                maximum=1.0,
                value=1.0,
                step=0.01,
                elem_id="top-p-slider",
                interactive=True
                )

                # Frequency Penalty Slider
                shared.gradio['frequency_penalty'] = gr.Slider(
                    label="Frequency Penalty",
                    minimum=0.0,
                    maximum=2.0,
                    value=0.0,
                    step=0.01,
                    elem_id="frequency-penalty-slider",
                    interactive=True
                )

                # Presence Penalty Slider
                shared.gradio['presence_penalty'] = gr.Slider(
                    label="Presence Penalty",
                    minimum=0.0,
                    maximum=2.0,
                    value=0.0,
                    step=0.01,
                    elem_id="presence-penalty-slider",
                    interactive=True
                )
                shared.gradio['custom_stopping_strings'] = gr.Textbox(
                    label="Stop Sequences (comma-separated)",
                    placeholder="Enter sequences and press Tab",
                    elem_id="stop-sequences-box",
                    interactive=True
                )

        with gr.Row():
            with gr.Column(elem_id='chat-col'):
                shared.gradio['display'] = gr.HTML(value=chat_html_wrapper({'internal': [], 'visible': []}, '', '', 'chat', 'classic-chat', ''))

                with gr.Row(elem_id="chat-input-row"):
                    with gr.Column(scale=1, elem_id='gr-hover-container'):
                        gr.HTML(value='<div class="hover-element" onclick="void(0)"><span style="width: 100px; display: block" id="hover-element-button">&#9776;</span><div class="hover-menu" id="hover-menu"></div>', elem_id='gr-hover')

                    with gr.Column(scale=10, elem_id='chat-input-container'):
                        shared.gradio['textbox'] = gr.Textbox(label='', placeholder='Send a message', elem_id='chat-input', elem_classes=['add_scrollbar'])
                        shared.gradio['show_controls'] = gr.Checkbox(value=shared.settings['show_controls'], label='Show controls (Ctrl+S)', elem_id='show-controls')
                        shared.gradio['typing-dots'] = gr.HTML(value='<div class="typing"><span></span><span class="dot1"></span><span class="dot2"></span></div>', label='typing', elem_id='typing-container')

                    with gr.Column(scale=1, elem_id='generate-stop-container'):
                        with gr.Row():
                            shared.gradio['Stop'] = gr.Button('Stop', elem_id='stop', visible=False)
                            shared.gradio['Generate'] = gr.Button('Generate', elem_id='Generate', variant='primary')

        with gr.Row(elem_id='chat-controls', elem_classes=['pretty_scrollbar']):
            with gr.Column():

                with gr.Row():
                    shared.gradio['mode'] = gr.Radio(choices=['equivariant-encrypt'], value=shared.settings['mode'] if shared.settings['mode'] in ['chat', 'equivariant-encrypt'] else None, label='Encrypted Model', info='Your data insertions, prompts and responses remain fully encrypted, blind to your cloud provider and the AI inference provider.', elem_id='chat-mode')

                with gr.Row():
                    shared.gradio['chat_style'] = gr.Dropdown(choices=utils.get_available_chat_styles(), label='Chat Theme', value=shared.settings['chat_style'], visible=shared.settings['mode'] != 'instruct')
                    shared.gradio['character'] = gr.Dropdown(choices=['Assistant'],info="Used in chat and equivariant-encrypt modes.",label='Character', value='Assistant', visible=True, interactive=True)

                with gr.Row():
                    shared.gradio['equivariant-encrypt_command'] = gr.Textbox(value=shared.settings['equivariant-encrypt_command'], lines=12, label='System Prompt', info='\n', visible=shared.settings['mode'] == 'equivariant-encrypt', elem_classes=['add_scrollbar'])
with gr.Box(visible=False):
    gr.HTML("""
    <script>
    window.addEventListener('load', function() {
        let interval = setInterval(function(){
            let btn = document.getElementById("start-new-chat");
            if (btn) {
                console.log("Auto-clicked 'New chat' button.");
                btn.click();
                clearInterval(interval);
            }
        }, 200);
    });
    </script>
    """)
def create_chat_settings_ui():
    mu = shared.args.multi_user
    with gr.Tab('Chat'):
        with gr.Row():
            with gr.Column(scale=8):
                with gr.Tab("Character"):
                    with gr.Row():
                        shared.gradio['character_menu'] = gr.Dropdown(value=None, choices=utils.get_available_characters(), label='Character', elem_id='character-menu', info='Used in chat and equivariant-encrypt modes.', elem_classes='slim-dropdown',visible=False)
                        ui.create_refresh_button(shared.gradio['character_menu'], lambda: None, lambda: {'choices': utils.get_available_characters()}, 'refresh-button', interactive=True)
                        shared.gradio['save_character'] = gr.Button('💾', elem_classes='refresh-button', elem_id="save-character", interactive=not mu,visible=False)
                        shared.gradio['delete_character'] = gr.Button('🗑️', elem_classes='refresh-button', interactive=not mu,visible=False)

                    shared.gradio['name2'] = gr.Textbox(value='', lines=1, label='Character\'s name')
                    shared.gradio['context'] = gr.Textbox(value='', lines=10, label='Context', elem_classes=['add_scrollbar'])
                    shared.gradio['greeting'] = gr.Textbox(value='', lines=5, label='Greeting', elem_classes=['add_scrollbar'])

                with gr.Tab("User"):
                    shared.gradio['name1'] = gr.Textbox(value=shared.settings['name1'], lines=1, label='Name')
                    shared.gradio['user_bio'] = gr.Textbox(value=shared.settings['user_bio'], lines=10, label='Description', info='Here you can optionally write a description of yourself.', placeholder='{{user}}\'s personality: ...', elem_classes=['add_scrollbar'])

                with gr.Tab('Chat history'):
                    with gr.Row():
                        with gr.Column():
                            shared.gradio['save_chat_history'] = gr.Button(value='Save history')

                        with gr.Column():
                            shared.gradio['load_chat_history'] = gr.File(type='binary', file_types=['.json', '.txt'], label='Upload History JSON')

                with gr.Tab('Upload character'):
                    with gr.Tab('YAML or JSON'):
                        with gr.Row():
                            shared.gradio['upload_json'] = gr.File(type='binary', file_types=['.json', '.yaml'], label='JSON or YAML File', interactive=not mu)
                            shared.gradio['upload_img_bot'] = gr.Image(type='pil', label='Profile Picture (optional)', interactive=not mu)

                        shared.gradio['Submit character'] = gr.Button(value='Submit', interactive=False)

                    with gr.Tab('TavernAI PNG'):
                        with gr.Row():
                            with gr.Column():
                                shared.gradio['upload_img_tavern'] = gr.Image(type='pil', label='TavernAI PNG File', elem_id='upload_img_tavern', interactive=not mu)
                                shared.gradio['tavern_json'] = gr.State()
                            with gr.Column():
                                shared.gradio['tavern_name'] = gr.Textbox(value='', lines=1, label='Name', interactive=False)
                                shared.gradio['tavern_desc'] = gr.Textbox(value='', lines=10, label='Description', interactive=False, elem_classes=['add_scrollbar'])

                        shared.gradio['Submit tavern character'] = gr.Button(value='Submit', interactive=False)

            with gr.Column(scale=1):
                shared.gradio['character_picture'] = gr.Image(label='Character picture', type='pil', interactive=not mu)
                shared.gradio['your_picture'] = gr.Image(label='Your picture', type='pil', value=Image.open(Path('cache/pfp_me.png')) if Path('cache/pfp_me.png').exists() else None, interactive=not mu)

    with gr.Tab('Instruction template'):
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    shared.gradio['instruction_template'] = gr.Dropdown(choices=utils.get_available_instruction_templates(), label='Saved instruction templates', info="After selecting the template, click on \"Load\" to load and apply it.", value='None', elem_classes='slim-dropdown')
                    ui.create_refresh_button(shared.gradio['instruction_template'], lambda: None, lambda: {'choices': utils.get_available_instruction_templates()}, 'refresh-button', interactive=not mu)
                    shared.gradio['load_template'] = gr.Button("Load", elem_classes='refresh-button')
                    shared.gradio['save_template'] = gr.Button('💾', elem_classes='refresh-button', interactive=not mu)
                    shared.gradio['delete_template'] = gr.Button('🗑️ ', elem_classes='refresh-button', interactive=not mu)

            with gr.Column():
                pass

        with gr.Row():
            with gr.Column():
                shared.gradio['custom_system_message'] = gr.Textbox(value=shared.settings['custom_system_message'], lines=2, label='Custom system message', info='If not empty, will be used instead of the default one.', elem_classes=['add_scrollbar'])
                shared.gradio['instruction_template_str'] = gr.Textbox(value='', label='Instruction template', lines=24, info='Change this according to the model/LoRA that you are using. Used in instruct and equivariant-encrypt modes.', elem_classes=['add_scrollbar', 'monospace'])
                with gr.Row():
                    shared.gradio['send_instruction_to_default'] = gr.Button('Send to default', elem_classes=['small-button'])
                    shared.gradio['send_instruction_to_notebook'] = gr.Button('Send to notebook', elem_classes=['small-button'])
                    shared.gradio['send_instruction_to_negative_prompt'] = gr.Button('Send to negative prompt', elem_classes=['small-button'])

            with gr.Column():
                shared.gradio['chat_template_str'] = gr.Textbox(value=shared.settings['chat_template_str'], label='Chat template', lines=22, elem_classes=['add_scrollbar', 'monospace'])

def create_event_handlers():

    # Obsolete variables, kept for compatibility with old extensions
    shared.input_params = gradio(inputs)
    shared.reload_inputs = gradio(reload_arr)
    shared.gradio['Generate'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state'),
        concurrency_limit=20).then(
        lambda x: (x, ''), gradio('textbox'), gradio('Chat input', 'textbox'), show_progress=False).then(
        lambda: None, None, None, js='() => document.getElementById("chat").parentNode.parentNode.parentNode.classList.add("_generating")').then(
        chat.generate_chat_reply_wrapper, gradio(inputs), gradio('display', 'history'), show_progress=False).then(
        None, None, None, js='() => document.getElementById("chat").parentNode.parentNode.parentNode.classList.remove("_generating")').then(
        None, None, None, js=f'() => {{{ui.audio_notification_js}}}')


    shared.gradio['Output Off'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')
    ).then(
        ui.toggle_tokenize, gradio('interface_state') , gradio('tokenize')
    ).then(
        chat.toggle_tokenize_text, gradio('interface_state'), gradio('display', 'history'), show_progress=False
    )

    shared.gradio['Output On'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')
    ).then(
        ui.toggle_tokenize, gradio('interface_state') , gradio('tokenize')
    ).then(
        chat.toggle_detokenize_text, gradio('interface_state'), gradio('display', 'history'), show_progress=False
    )



    shared.gradio['textbox'].submit(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        lambda x: (x, ''), gradio('textbox'), gradio('Chat input', 'textbox'), show_progress=False).then(
        lambda: None, None, None, js='() => document.getElementById("chat").parentNode.parentNode.parentNode.classList.add("_generating")').then(
        chat.generate_chat_reply_wrapper, gradio(inputs), gradio('display', 'history'), show_progress=False).then(
        None, None, None, js='() => document.getElementById("chat").parentNode.parentNode.parentNode.classList.remove("_generating")').then(
        None, None, None, js=f'() => {{{ui.audio_notification_js}}}')
    # shared.gradio['Remove last'].click(
    #     ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #     chat.handle_remove_last_click, gradio('interface_state'), gradio('history', 'display', 'textbox'), show_progress=False)

    shared.gradio['Stop'].click(
        stop_everything_event, None, None, queue=False).then(
        chat.redraw_html, gradio(reload_arr), gradio('display'), show_progress=False)

    if not shared.args.multi_user:
        shared.gradio['unique_id'].select(
            ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
            chat.handle_unique_id_select, gradio('interface_state'), gradio('history', 'display'), show_progress=False)

    # shared.gradio['Start new chat'].click(
    #     ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #     chat.handle_start_new_chat_click, gradio('interface_state'), gradio('history', 'display', 'unique_id'), show_progress=False)

    # shared.gradio['delete_chat'].click(lambda: gr.update(visible=True), None, gradio('delete-chat-row'))
    # shared.gradio['delete_chat-cancel'].click(lambda: gr.update(visible=False), None, gradio('delete-chat-row'))
    # shared.gradio['delete_chat-confirm'].click(
    #     ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #     chat.handle_delete_chat_confirm_click, gradio('interface_state'), gradio('history', 'display', 'unique_id', 'delete-chat-row'), show_progress=False)

    # shared.gradio['rename_chat'].click(chat.handle_rename_chat_click, None, gradio('rename_to', 'rename-row'), show_progress=False)
    # shared.gradio['rename_to-cancel'].click(lambda: gr.update(visible=False), None, gradio('rename-row'), show_progress=False)
    # shared.gradio['rename_to-confirm'].click(
    #     ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #     chat.handle_rename_chat_confirm, gradio('rename_to', 'interface_state'), gradio('unique_id', 'rename-row'))

    # shared.gradio['rename_to'].submit(
    #     ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #     chat.handle_rename_chat_confirm, gradio('rename_to', 'interface_state'), gradio('unique_id', 'rename-row'), show_progress=False)

    shared.gradio['load_chat_history'].upload(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.handle_upload_chat_history, gradio('load_chat_history', 'interface_state'), gradio('history', 'display'), show_progress=False).then(
        None, None, None, js=f'() => {{{ui.switch_tabs_js}; switch_to_chat()}}')

    # shared.gradio['character_menu'].change(
    #     ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #     chat.handle_character_menu_change, gradio('interface_state'), gradio('history', 'display', 'name1', 'name2', 'character_picture', 'greeting', 'context'), show_progress=False).then(
    #     None, None, None, js=f'() => {{{ui.update_big_picture_js}; updateBigPicture()}}')

    shared.gradio['mode'].change(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        chat.handle_mode_change, gradio('interface_state'), gradio('history', 'display', 'chat_style', 'equivariant-encrypt_command'), show_progress=False).then(
        None, gradio('mode'), None, js="(mode) => {mode === 'instruct' ? document.getElementById('character-menu').parentNode.parentNode.style.display = 'none' : document.getElementById('character-menu').parentNode.parentNode.style.display = ''}")

    shared.gradio['chat_style'].change(chat.redraw_html, gradio(reload_arr), gradio('display'), show_progress=False)

    # Save/delete a character
    # shared.gradio['save_character'].click(chat.handle_save_character_click, gradio('name2'), gradio('save_character_filename', 'character_saver'), show_progress=False)
    # shared.gradio['delete_character'].click(lambda: gr.update(visible=True), None, gradio('character_deleter'), show_progress=False)
    # shared.gradio['load_template'].click(chat.handle_load_template_click, gradio('instruction_template'), gradio('instruction_template_str', 'instruction_template'), show_progress=False)
    # shared.gradio['save_template'].click(
    #     ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #     chat.handle_save_template_click, gradio('instruction_template_str'), gradio('save_filename', 'save_root', 'save_contents', 'file_saver'), show_progress=False)

    # shared.gradio['delete_template'].click(chat.handle_delete_template_click, gradio('instruction_template'), gradio('delete_filename', 'delete_root', 'file_deleter'), show_progress=False)
    # shared.gradio['save_chat_history'].click(
    #     lambda x: json.dumps(x, indent=4), gradio('history'), gradio('temporary_text')).then(
    #     None, gradio('temporary_text', 'character_menu', 'mode'), None, js=f'(hist, char, mode) => {{{ui.save_files_js}; saveHistory(hist, char, mode)}}')

    # shared.gradio['Submit character'].click(
    #     chat.upload_character, gradio('upload_json', 'upload_img_bot'), gradio('character_menu'), show_progress=False).then(
    #     None, None, None, js=f'() => {{{ui.switch_tabs_js}; switch_to_character()}}')

    # shared.gradio['Submit tavern character'].click(
    #     chat.upload_tavern_character, gradio('upload_img_tavern', 'tavern_json'), gradio('character_menu'), show_progress=False).then(
    #     None, None, None, js=f'() => {{{ui.switch_tabs_js}; switch_to_character()}}')

    # shared.gradio['upload_json'].upload(lambda: gr.update(interactive=True), None, gradio('Submit character'))
    # shared.gradio['upload_json'].clear(lambda: gr.update(interactive=False), None, gradio('Submit character'))
    # shared.gradio['upload_img_tavern'].upload(chat.check_tavern_character, gradio('upload_img_tavern'), gradio('tavern_name', 'tavern_desc', 'tavern_json', 'Submit tavern character'), show_progress=False)
    # shared.gradio['upload_img_tavern'].clear(lambda: (None, None, None, gr.update(interactive=False)), None, gradio('tavern_name', 'tavern_desc', 'tavern_json', 'Submit tavern character'), show_progress=False)
    # shared.gradio['your_picture'].change(
    #     ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #     chat.handle_your_picture_change, gradio('your_picture', 'interface_state'), gradio('display'), show_progress=False)
    
    # shared.gradio['send_instruction_to_negative_prompt'].click(
    #     ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
    #     chat.handle_send_instruction_click, gradio('interface_state'), gradio('negative_prompt'), show_progress=False).then(
    #     None, None, None, js=f'() => {{{ui.switch_tabs_js}; switch_to_generation_parameters()}}')
        
    # shared.gradio['show_controls'].change(None, gradio('show_controls'), None, js=f'(x) => {{{ui.show_controls_js}; toggle_controls(x)}}')
