from strings import TITLE, ABSTRACT, BOTTOM_LINE
from strings import DEFAULT_EXAMPLES
from styles import PARENT_BLOCK_CSS

import argparse
import gradio as gr

from model import load_model
from gen import get_output
from utils import generate_prompt, post_processes

def chat(
    contexts,
    instructions, 
    state_chatbots
):
    print("-------state_chatbots------")
    print(state_chatbots)
    results = []

    instruct_prompts = [
        generate_prompt(instruct, histories, ctx) 
        for ctx, instruct, histories in zip(contexts, instructions, state_chatbots)
    ]
        
    bot_responses = get_output(
        model, tokenizer, instruct_prompts, None
    )
    print(bot_responses)
    bot_responses = post_processes(bot_responses)

    print("zipping...")
    sub_results = []
    for instruction, bot_response, state_chatbot in zip(instructions, bot_responses, state_chatbots):
        print(instruction)
        print(bot_response)
        print(state_chatbot)
        new_state_chatbot = state_chatbot + [(instruction, bot_response)]
        print(new_state_chatbot)
        results.append(new_state_chatbot)

    print(results)
    print(len(results))

    return (results, results)

def reset_textbox():
    return gr.Textbox.update(value='')

def parse_args():
    parser = argparse.ArgumentParser(
        description="Gradio Application for Alpaca-LoRA as a chatbot service"
    )
    # Dataset related.
    parser.add_argument(
        "--base_url",
        help="huggingface hub url",
        default="decapoda-research/llama-7b-hf",
        type=str,
    )
    parser.add_argument(
        "--ft_ckpt_url",
        help="huggingface hub url",
        default="tloen/alpaca-lora-7b",
        type=str,
    )
    parser.add_argument(
        "--port",
        help="port to serve app",
        default=6006,
        type=int,
    )
    parser.add_argument(
        "--api_open",
        help="do you want to open as API",
        default="no",
        type=str,
    )
    parser.add_argument(
        "--share",
        help="do you want to share temporarily",
        default="no",
        type=str
    )

    return parser.parse_args()

def run(args):
    global model, tokenizer

    model, tokenizer = load_model(
        base=args.base_url,
        finetuned=args.ft_ckpt_url
    )

    with gr.Blocks(css=PARENT_BLOCK_CSS) as demo:
        state_chatbot = gr.State([])

        with gr.Column(elem_id='col_container'):
            gr.Markdown(f"## {TITLE}\n\n\n{ABSTRACT}")

            with gr.Accordion("Context Setting", open=False):
                context_txtbox = gr.Textbox(placeholder="Surrounding information to AI", label="Enter Context")
                hidden_txtbox = gr.Textbox(placeholder="", label="Order", visible=False)

            chatbot = gr.Chatbot(elem_id='chatbot', label="Alpaca-LoRA")
            instruction_txtbox = gr.Textbox(placeholder="What do you want to say to AI?", label="Instruction")
            send_prompt_btn = gr.Button(value="Send Prompt")

            gr.Examples(
                examples=DEFAULT_EXAMPLES, 
                inputs=[
                    hidden_txtbox, instruction_txtbox
                ],
                label="Examples. ▶️ symbol indicates follow-up prompts"
            )

            gr.Markdown(f"{BOTTOM_LINE}")

        send_prompt_btn.click(
            chat, 
            [context_txtbox, instruction_txtbox, state_chatbot],
            [state_chatbot, chatbot],
            batch=True,
            max_batch_size=4,
            api_name="text_gen"
        )
        send_prompt_btn.click(
            reset_textbox, 
            [], 
            [instruction_txtbox],
        )

    demo.queue(
        api_open=False if args.api_open == "no" else True
    ).launch(
        share=False if args.share == "no" else True,
        server_port=args.port
    )

if __name__ == "__main__":
    args = parse_args()
    run(args)
