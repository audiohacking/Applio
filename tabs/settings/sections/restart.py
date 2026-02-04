import gradio as gr
import os
import sys
import json

from app_paths import get_app_support_dir

now_dir = os.getcwd()


def stop_train(model_name: str):
    pid_file_path = os.path.join(get_app_support_dir(), "logs", model_name, "config.json")
    try:
        with open(pid_file_path, "r") as pid_file:
            pid_data = json.load(pid_file)
            pids = pid_data.get("process_pids", [])
        with open(pid_file_path, "w") as pid_file:
            pid_data.pop("process_pids", None)
            json.dump(pid_data, pid_file, indent=4)
        for pid in pids:
            os.kill(pid, 9)
    except:
        pass


def stop_infer():
    pid_file_path = os.path.join(now_dir, "assets", "infer_pid.txt")
    try:
        with open(pid_file_path, "r") as pid_file:
            pids = [int(pid) for pid in pid_file.readlines()]
        for pid in pids:
            os.kill(pid, 9)
        os.remove(pid_file_path)
    except:
        pass


def restart_applio():
    # When running as the bundled app, do not exec/restart — that can cause a second
    # instance or relaunch issues. User should quit and reopen the app.
    if getattr(sys, "frozen", False):
        raise gr.Error(
            "When running as the Applio app, please quit (Cmd+Q or close the window) and reopen Applio to restart. "
            "Do not use Restart from within the app."
        )
    if os.name != "nt":
        os.system("clear")
    else:
        os.system("cls")
    python = sys.executable
    os.execl(python, python, *sys.argv)


from assets.i18n.i18n import I18nAuto

i18n = I18nAuto()


def restart_tab():
    with gr.Row():
        with gr.Column():
            restart_button = gr.Button(i18n("Restart Applio"))
            restart_button.click(
                fn=restart_applio,
                inputs=[],
                outputs=[],
            )
