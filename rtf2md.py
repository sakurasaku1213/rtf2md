import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext # 結果表示用にscrolledtextをインポート
import pypandoc
import os

# Pandocが利用可能か事前にチェック
try:
    # pypandoc が Pandoc を見つけられるか試す
    # (バージョンによっては get_pandoc_path() がない場合もあるので、より汎用的なチェック方法も考慮)
    pypandoc.get_pandoc_version()
except OSError:
    messagebox.showerror("エラー", "Pandocが見つかりません。\nPandocをインストールして、システムパスが通っているか確認してください。")
    # Pandocが見つからない場合はアプリを終了する
    exit()

# 選択されたファイルパスのリストを保持する変数
selected_rtf_filepaths = []

def select_rtf_files_action():
    """
    複数RTFファイル選択ダイアログを開き、選択されたファイルパスをリストに格納する。
    選択されたファイル名をGUIに表示する。
    """
    global selected_rtf_filepaths
    # askopenfilenamesは選択されたファイルのパスのタプルを返す
    filepaths_tuple = filedialog.askopenfilenames(
        title="RTFファイルを選択 (複数選択可)",
        filetypes=(("RTFファイル", "*.rtf"), ("すべてのファイル", "*.*"))
    )
    if filepaths_tuple:
        selected_rtf_filepaths = list(filepaths_tuple) # タプルをリストに変換
        # 選択されたファイル名をGUIに表示（先頭のいくつか、またはファイル数）
        if len(selected_rtf_filepaths) > 3:
            display_files = ", ".join([os.path.basename(f) for f in selected_rtf_filepaths[:3]]) + f", 他 {len(selected_rtf_filepaths) - 3}件"
        else:
            display_files = ", ".join([os.path.basename(f) for f in selected_rtf_filepaths])
        selected_files_var.set(f"{len(selected_rtf_filepaths)} 個のファイルを選択: {display_files}")
    else:
        selected_rtf_filepaths = []
        selected_files_var.set("ファイルが選択されていません")

def convert_files_action():
    """
    選択されたRTFファイルをMarkdownに変換する。
    結果はGUIのテキストエリアに表示する。
    """
    global selected_rtf_filepaths
    if not selected_rtf_filepaths:
        messagebox.showwarning("ファイル未選択", "変換するRTFファイルを選択してください。")
        return

    # 結果表示テキストエリアを有効化してクリア
    results_log_text.config(state=tk.NORMAL)
    results_log_text.delete('1.0', tk.END)
    results_log_text.insert(tk.END, "変換処理を開始します...\n")

    success_count = 0
    failure_count = 0

    for rtf_path in selected_rtf_filepaths:
        # 出力ファイル名を生成 (入力ファイルと同じディレクトリ、拡張子.md)
        output_md_path = os.path.splitext(rtf_path)[0] + ".md"

        log_message_prefix = f"処理中: {os.path.basename(rtf_path)} -> {os.path.basename(output_md_path)}\n"
        results_log_text.insert(tk.END, log_message_prefix)
        root.update_idletasks() # UIを即時更新

        try:
            if not os.path.exists(rtf_path):
                raise FileNotFoundError("指定されたRTFファイルが見つかりません。")

            pypandoc.convert_file(
                rtf_path,
                'markdown_strict', # GFMなど他のMarkdown方言も指定可能 'gfm'
                format='rtf',
                outputfile=output_md_path,
                extra_args=['--wrap=none'] # 必要に応じてPandocのオプションを追加
            )
            results_log_text.insert(tk.END, f"  -> 成功: {output_md_path} に保存しました。\n\n")
            success_count += 1
        except Exception as e:
            results_log_text.insert(tk.END, f"  -> 失敗: {e}\n\n")
            failure_count += 1
        results_log_text.see(tk.END) # 最新のログが見えるようにスクロール
        root.update_idletasks()

    final_summary = f"\n--- 変換処理完了 ---\n成功: {success_count}件\n失敗: {failure_count}件\n"
    results_log_text.insert(tk.END, final_summary)
    results_log_text.config(state=tk.DISABLED) # 編集不可に戻す

    messagebox.showinfo("変換完了", f"処理が完了しました。\n成功: {success_count}件, 失敗: {failure_count}件\n詳細はログを確認してください。")
    selected_rtf_filepaths = [] # 処理が終わったらリストをクリア
    selected_files_var.set("ファイルが選択されていません") # 表示をリセット

# --- GUIのセットアップ ---
root = tk.Tk()
root.title("RTF to Markdown 変換 (複数ファイル対応)")
root.geometry("600x450") # ウィンドウサイズを少し調整

# ファイル選択フレーム
selection_frame = tk.Frame(root, pady=10)
selection_frame.pack(fill=tk.X)

select_button = tk.Button(selection_frame, text="RTFファイルを選択...", command=select_rtf_files_action, width=20)
select_button.pack(side=tk.LEFT, padx=10)

selected_files_var = tk.StringVar()
selected_files_var.set("ファイルが選択されていません")
selected_files_label = tk.Label(selection_frame, textvariable=selected_files_var, anchor="w")
selected_files_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

# 変換実行ボタン
convert_button = tk.Button(root, text="選択したファイルをMarkdownに変換", command=convert_files_action, height=2)
convert_button.pack(pady=10, fill=tk.X, padx=10)

# 結果表示ログエリア
log_frame = tk.LabelFrame(root, text="処理ログ", padx=5, pady=5)
log_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

results_log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, height=15)
results_log_text.pack(fill=tk.BOTH, expand=True)

root.mainloop()