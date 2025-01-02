import importlib
import math
import re
import traceback
from functools import partial
from pathlib import Path

import gradio as gr
import psutil
import torch
from transformers import is_torch_npu_available, is_torch_xpu_available

from modules import loaders, shared, ui, utils
from modules.logging_colors import logger
from modules.LoRA import add_lora_to_model
from modules.models import load_model, unload_model
from modules.models_settings import (
    apply_model_settings_to_state,
    get_model_metadata,
    save_instruction_template,
    save_model_settings,
    update_model_parameters
)
from modules.utils import gradio


def create_ui():
    mu = shared.args.multi_user

    # Finding the default values for the GPU and CPU memories
    total_mem = []
    if is_torch_xpu_available():
        for i in range(torch.xpu.device_count()):
            total_mem.append(math.floor(torch.xpu.get_device_properties(i).total_memory / (1024 * 1024)))
    elif is_torch_npu_available():
        for i in range(torch.npu.device_count()):
            total_mem.append(math.floor(torch.npu.get_device_properties(i).total_memory / (1024 * 1024)))
    else:
        for i in range(torch.cuda.device_count()):
            total_mem.append(math.floor(torch.cuda.get_device_properties(i).total_memory / (1024 * 1024)))

    default_gpu_mem = []
    if shared.args.gpu_memory is not None and len(shared.args.gpu_memory) > 0:
        for i in shared.args.gpu_memory:
            if 'mib' in i.lower():
                default_gpu_mem.append(int(re.sub('[a-zA-Z ]', '', i)))
            else:
                default_gpu_mem.append(int(re.sub('[a-zA-Z ]', '', i)) * 1000)

    while len(default_gpu_mem) < len(total_mem):
        default_gpu_mem.append(0)

    total_cpu_mem = math.floor(psutil.virtual_memory().total / (1024 * 1024))
    if shared.args.cpu_memory is not None:
        default_cpu_mem = re.sub('[a-zA-Z ]', '', shared.args.cpu_memory)
    else:
        default_cpu_mem = 0

    with gr.Tab("Model", elem_id="model-tab"):
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    with gr.Column():
                        with gr.Row():
                            shared.gradio['model_menu'] = gr.Dropdown(choices=utils.get_available_models(), value=lambda: shared.model_name, label='Model', elem_classes='slim-dropdown', interactive=not mu)
                            ui.create_refresh_button(shared.gradio['model_menu'], lambda: None, lambda: {'choices': utils.get_available_models()}, 'refresh-button', interactive=not mu)
                            shared.gradio['load_model'] = gr.Button("Load", visible=not shared.settings['autoload_model'], elem_classes='refresh-button', interactive=not mu)
                            shared.gradio['unload_model'] = gr.Button("Unload", elem_classes='refresh-button', interactive=not mu)
                            shared.gradio['save_model_settings'] = gr.Button("Save", elem_classes='refresh-button', interactive=not mu)


        with gr.Row():
            with gr.Column():
                shared.gradio['loader'] = gr.Dropdown(label="Model loader", choices=loaders.loaders_and_params.keys(), value=list(loaders.loaders_and_params.keys())[0])
                with gr.Blocks():
                    with gr.Row():
                        with gr.Column():
                            with gr.Blocks():
                                for i in range(len(total_mem)):
                                    shared.gradio[f'gpu_memory_{i}'] = gr.Slider(label=f"gpu-memory in MiB for device :{i}", maximum=total_mem[i], value=default_gpu_mem[i])

                                shared.gradio['cpu_memory'] = gr.Slider(label="cpu-memory in MiB", maximum=total_cpu_mem, value=default_cpu_mem)

                            with gr.Blocks():
                                shared.gradio['transformers_info'] = gr.Markdown('load-in-4bit params:')
                                shared.gradio['compute_dtype'] = gr.Dropdown(label="compute_dtype", choices=["bfloat16", "float16", "float32"], value=shared.args.compute_dtype)
                                shared.gradio['quant_type'] = gr.Dropdown(label="quant_type", choices=["nf4", "fp4"], value=shared.args.quant_type)

                            hqq_backend_choices = ["PYTORCH", "PYTORCH_COMPILE", "ATEN"]
                            shared.gradio['hqq_backend'] = gr.Dropdown(label="hqq_backend", choices=hqq_backend_choices, value=hqq_backend_choices[0])
                            shared.gradio['n_ctx'] = gr.Number(label="Context Length", precision=0, step=256, value=shared.args.n_ctx, info='Context length. Try lowering this if you run out of memory while loading the model.')
                            shared.gradio['tensor_split'] = gr.Textbox(label='tensor_split', info='List of proportions to split the model across multiple GPUs. Example: 60,40')
                            shared.gradio['n_batch'] = gr.Slider(label="n_batch", minimum=1, maximum=2048, step=1, value=shared.args.n_batch)
                            shared.gradio['max_seq_len'] = gr.Number(label='max_seq_len', precision=0, step=256, value=shared.args.max_seq_len, info='Context length. Try lowering this if you run out of memory while loading the model.')

                        with gr.Column():
                            shared.gradio['load_in_8bit'] = gr.Checkbox(label="load-in-8bit", value=shared.args.load_in_8bit)
                            shared.gradio['load_in_4bit'] = gr.Checkbox(label="load-in-4bit", value=shared.args.load_in_4bit)
                            shared.gradio['use_double_quant'] = gr.Checkbox(label="use_double_quant", value=shared.args.use_double_quant)
                            shared.gradio['auto_devices'] = gr.Checkbox(label="auto-devices", value=shared.args.auto_devices)
                            shared.gradio['cache_type'] = gr.Dropdown(label="cache_type", choices=['fp16', 'q8_0', 'q4_0', 'fp8', 'q8', 'q6', 'q4'], value=shared.args.cache_type, info='Valid options: llama.cpp - fp16, q8_0, q4_0; ExLlamaV2 - fp16, fp8, q8, q6, q4.')
                            shared.gradio['streaming_llm'] = gr.Checkbox(label="streaming_llm", value=shared.args.streaming_llm, info='(experimental) Activate StreamingLLM to avoid re-evaluating the entire prompt when old messages are removed.')
                            shared.gradio['cpu'] = gr.Checkbox(label="cpu", value=shared.args.cpu, info='llama.cpp: Use llama-cpp-python compiled without GPU acceleration. Transformers: use PyTorch in CPU mode.')
                            shared.gradio['row_split'] = gr.Checkbox(label="row_split", value=shared.args.row_split, info='Split the model by rows across GPUs. This may improve multi-gpu performance.')
                            shared.gradio['no_use_cuda_fp16'] = gr.Checkbox(label="no_use_cuda_fp16", value=shared.args.no_use_cuda_fp16, info='This can make models faster on some systems.')
                            shared.gradio['disk'] = gr.Checkbox(label="disk", value=shared.args.disk)
                            shared.gradio['bf16'] = gr.Checkbox(label="bf16", value=shared.args.bf16)
                            shared.gradio['enable_tp'] = gr.Checkbox(label="enable_tp", value=shared.args.enable_tp, info='Enable Tensor Parallelism (TP).')
                            with gr.Blocks():
                                shared.gradio['trust_remote_code'] = gr.Checkbox(label="trust-remote-code", value=shared.args.trust_remote_code, info='Set trust_remote_code=True while loading the tokenizer/model. To enable this option, start the web UI with the --trust-remote-code flag.', interactive=shared.args.trust_remote_code)
                                shared.gradio['no_use_fast'] = gr.Checkbox(label="no_use_fast", value=shared.args.no_use_fast, info='Set use_fast=False while loading the tokenizer.')
            with gr.Column():
                with gr.Row():
                    shared.gradio['autoload_model'] = gr.Checkbox(value=shared.settings['autoload_model'], label='Autoload the model', info='Whether to load the model as soon as it is selected in the Model dropdown.', interactive=not mu)

                with gr.Tab("Download"):
                    shared.gradio['custom_model_menu'] = gr.Textbox(label="Download model or LoRA",info="Enter the Hugging Face username/model path, for instance: facebook/galactica-125m. To specify a branch, add it at the end after a \":\" character like this: facebook/galactica-125m:main. To download a single file, enter its name in the second box.", interactive=False)
                    shared.gradio['download_specific_file'] = gr.Textbox(placeholder="File name (for GGUF models)", show_label=False, max_lines=1, interactive=False)
                    with gr.Row():
                        shared.gradio['download_model_button'] = gr.Button("Download", variant='primary', interactive=False)
                        shared.gradio['get_file_list'] = gr.Button("Get file list", interactive=False)

                with gr.Row():
                    shared.gradio['model_status'] = gr.Markdown('' if shared.model_name == 'None' else 'Ready')


def create_event_handlers():
    shared.gradio['loader'].change(loaders.make_loader_params_visible, gradio('loader'), gradio(loaders.get_all_params()), show_progress=False)

    # In this event handler, the interface state is read and updated
    # with the model defaults (if any), and then the model is loaded
    # unless "autoload_model" is unchecked
    shared.gradio['model_menu'].change(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        handle_load_model_event_initial, gradio('model_menu', 'interface_state'), gradio(ui.list_interface_input_elements()) + gradio('interface_state'), show_progress=False).then(
        load_model_wrapper, gradio('model_menu', 'loader', 'autoload_model'), gradio('model_status'), show_progress=True).success(
        handle_load_model_event_final, gradio('truncation_length', 'loader', 'interface_state'), gradio('truncation_length', 'filter_by_loader'), show_progress=False)

    shared.gradio['load_model'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        update_model_parameters, gradio('interface_state'), None).then(
        partial(load_model_wrapper, autoload=True), gradio('model_menu', 'loader'), gradio('model_status'), show_progress=True).success(
        handle_load_model_event_final, gradio('truncation_length', 'loader', 'interface_state'), gradio('truncation_length', 'filter_by_loader'), show_progress=False)

    shared.gradio['unload_model'].click(handle_unload_model_click, None, gradio('model_status'), show_progress=False)
    shared.gradio['save_model_settings'].click(
        ui.gather_interface_values, gradio(shared.input_elements), gradio('interface_state')).then(
        save_model_settings, gradio('model_menu', 'interface_state'), gradio('model_status'), show_progress=False)

    shared.gradio['download_model_button'].click(download_model_wrapper, gradio('custom_model_menu', 'download_specific_file'), gradio('model_status'), show_progress=True)
    shared.gradio['get_file_list'].click(partial(download_model_wrapper, return_links=True), gradio('custom_model_menu', 'download_specific_file'), gradio('model_status'), show_progress=True)
    shared.gradio['autoload_model'].change(lambda x: gr.update(visible=not x), gradio('autoload_model'), gradio('load_model'))


def load_model_wrapper(selected_model, loader, autoload=False):
    if not autoload:
        yield f"The settings for `{selected_model}` have been updated.\n\nClick on \"Load\" to load it."
        return

    if selected_model == 'None':
        yield "No model selected"
    else:
        try:
            yield f"Loading `{selected_model}`..."
            unload_model()
            if selected_model != '':
                shared.model, shared.tokenizer = load_model(selected_model, loader)

            if shared.model is not None:
                output = f"Successfully loaded `{selected_model}`."

                settings = get_model_metadata(selected_model)
                if 'instruction_template' in settings:
                    output += '\n\nIt seems to be an instruction-following model with template "{}". In the chat tab, instruct or chat-instruct modes should be used.'.format(settings['instruction_template'])

                yield output
            else:
                yield f"Failed to load `{selected_model}`."
        except:
            exc = traceback.format_exc()
            logger.error('Failed to load the model.')
            print(exc)
            yield exc.replace('\n', '\n\n')


def load_lora_wrapper(selected_loras):
    yield ("Applying the following LoRAs to {}:\n\n{}".format(shared.model_name, '\n'.join(selected_loras)))
    add_lora_to_model(selected_loras)
    yield ("Successfuly applied the LoRAs")


def download_model_wrapper(repo_id, specific_file, progress=gr.Progress(), return_links=False, check=False):
    try:
        if repo_id == "":
            yield ("Please enter a model path")
            return

        repo_id = repo_id.strip()
        specific_file = specific_file.strip()
        downloader = importlib.import_module("download-model").ModelDownloader()

        progress(0.0)
        model, branch = downloader.sanitize_model_and_branch_names(repo_id, None)

        yield ("Getting the download links from Hugging Face")
        links, sha256, is_lora, is_llamacpp = downloader.get_download_links_from_huggingface(model, branch, text_only=False, specific_file=specific_file)
        if return_links:
            output = "```\n"
            for link in links:
                output += f"{Path(link).name}" + "\n"

            output += "```"
            yield output
            return

        yield ("Getting the output folder")
        output_folder = downloader.get_output_folder(
            model,
            branch,
            is_lora,
            is_llamacpp=is_llamacpp,
            model_dir=shared.args.model_dir if shared.args.model_dir != shared.args_defaults.model_dir else None
        )

        if output_folder == Path("models"):
            output_folder = Path(shared.args.model_dir)
        elif output_folder == Path("loras"):
            output_folder = Path(shared.args.lora_dir)

        if check:
            progress(0.5)

            yield ("Checking previously downloaded files")
            downloader.check_model_files(model, branch, links, sha256, output_folder)
            progress(1.0)
        else:
            yield (f"Downloading file{'s' if len(links) > 1 else ''} to `{output_folder}/`")
            downloader.download_model_files(model, branch, links, sha256, output_folder, progress_bar=progress, threads=4, is_llamacpp=is_llamacpp)

            yield (f"Model successfully saved to `{output_folder}/`.")
    except:
        progress(1.0)
        yield traceback.format_exc().replace('\n', '\n\n')


def create_llamacpp_hf(gguf_name, unquantized_url, progress=gr.Progress()):
    try:
        downloader = importlib.import_module("download-model").ModelDownloader()

        progress(0.0)
        model, branch = downloader.sanitize_model_and_branch_names(unquantized_url, None)

        yield ("Getting the tokenizer files links from Hugging Face")
        links, sha256, is_lora, is_llamacpp = downloader.get_download_links_from_huggingface(model, branch, text_only=True)
        output_folder = Path(shared.args.model_dir) / (re.sub(r'(?i)\.gguf$', '', gguf_name) + "-HF")

        yield (f"Downloading tokenizer to `{output_folder}/`")
        downloader.download_model_files(model, branch, links, sha256, output_folder, progress_bar=progress, threads=4, is_llamacpp=False)

        # Move the GGUF
        (Path(shared.args.model_dir) / gguf_name).rename(output_folder / gguf_name)

        yield (f"Model saved to `{output_folder}/`.\n\nYou can now load it using llamacpp_HF.")
    except:
        progress(1.0)
        yield traceback.format_exc().replace('\n', '\n\n')


def update_truncation_length(current_length, state):
    if 'loader' in state:
        if state['loader'].lower().startswith('exllama'):
            return state['max_seq_len']
        elif state['loader'] in ['llama.cpp', 'llamacpp_HF']:
            return state['n_ctx']

    return current_length


def handle_load_model_event_initial(model, state):
    state = apply_model_settings_to_state(model, state)
    output = ui.apply_interface_values(state)
    update_model_parameters(state)
    return output + [state]


def handle_load_model_event_final(truncation_length, loader, state):
    truncation_length = update_truncation_length(truncation_length, state)
    return [truncation_length, loader]


def handle_unload_model_click():
    unload_model()
    return "Model unloaded"
