import os
import sys
import gradio as gr
from pathlib import Path

from assets.i18n.i18n import I18nAuto

now_dir = os.getcwd()
sys.path.append(now_dir)

i18n = I18nAuto()


def get_console_log_path():
    """Get the console log file path. Works for both bundled and script mode."""
    if getattr(sys, "frozen", False):
        # Running as bundled app - logs are in ~/Library/Logs/Applio/
        home_dir = Path.home()
        log_path = home_dir / "Library" / "Logs" / "Applio" / "console.log"
    else:
        # Running as script - use logs directory in project
        log_path = Path(now_dir) / "logs" / "console.log"

    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create log file if it doesn't exist
    if not log_path.exists():
        log_path.touch()

    return str(log_path)


def read_console_log(lines=100):
    """Read the last N lines from the console log."""
    try:
        log_path = get_console_log_path()
        if not os.path.exists(log_path):
            return (
                "Console log file not found. The app may not have started logging yet."
            )

        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            # Read all lines and get the last N
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

            if not last_lines:
                return "Console log is empty. Waiting for output..."

            return "".join(last_lines)
    except Exception as e:
        return f"Error reading console log: {str(e)}"


def clear_console_log():
    """Clear the console log file."""
    try:
        log_path = get_console_log_path()
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("")
        return "Console log cleared successfully."
    except Exception as e:
        return f"Error clearing console log: {str(e)}"


def console_tab():
    with gr.Column():
        gr.Markdown(
            i18n(
                "## Console Output\n"
                "View real-time console output from Applio. This shows all Python output including model loading, training progress, and errors."
            )
        )

        with gr.Row():
            lines_slider = gr.Slider(
                minimum=50,
                maximum=1000,
                value=200,
                step=50,
                label=i18n("Number of lines to display"),
                info=i18n("Show the last N lines from the console log"),
            )

        with gr.Row():
            refresh_btn = gr.Button(i18n("🔄 Refresh"), variant="primary")
            clear_btn = gr.Button(i18n("🗑️ Clear Log"), variant="secondary")
            auto_refresh = gr.Checkbox(
                label=i18n("Auto-refresh (every 2 seconds)"), value=False
            )

        console_output = gr.Textbox(
            label=i18n("Console Log"),
            lines=25,
            max_lines=50,
            value=read_console_log(200),
            interactive=False,
            elem_classes=["console-output"],
        )

        with gr.Accordion(i18n("ℹ️ Console Information"), open=False):
            gr.Markdown(
                i18n(
                    "### About the Console\n\n"
                    "The console displays all output from Applio, including:\n"
                    "- **Model Loading**: Progress of model initialization\n"
                    "- **Training**: Epoch progress, loss values, and training metrics\n"
                    "- **Inference**: Processing status and completion messages\n"
                    "- **Errors**: Detailed error messages and stack traces\n"
                    "- **System Info**: GPU/CPU usage, memory statistics\n\n"
                    "**Log Location**:\n"
                    f"- Bundled App: `~/Library/Logs/Applio/console.log`\n"
                    f"- Script Mode: `{os.path.join(now_dir, 'logs', 'console.log')}`\n\n"
                    "**Tips**:\n"
                    "- Use auto-refresh to monitor long-running tasks\n"
                    "- Increase line count to see more history\n"
                    "- Copy output to share error messages\n"
                    "- Clear log to reset and reduce file size"
                )
            )

        # Event handlers
        def refresh_console(lines):
            return read_console_log(int(lines))

        def handle_clear():
            clear_console_log()
            gr.Info(i18n("Console log cleared successfully."))
            return read_console_log(200)

        refresh_btn.click(
            fn=refresh_console, inputs=[lines_slider], outputs=[console_output]
        )

        clear_btn.click(fn=handle_clear, outputs=[console_output])

        # Auto-refresh: use gr.Timer (documented) to poll every 2s when enabled
        def auto_refresh_func(enabled, lines):
            if enabled:
                return refresh_console(lines)
            return gr.update()

        timer = gr.Timer(value=2)
        timer.tick(
            fn=auto_refresh_func,
            inputs=[auto_refresh, lines_slider],
            outputs=[console_output],
        )
