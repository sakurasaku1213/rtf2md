import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk # ttk（テーマ付きwidget）を追加
import pypandoc
import os
import sys
import json
import datetime
import re
import tempfile  # 一時ファイル作成用
from pathlib import Path
import threading  # バックグラウンド処理用
import time
import logging  # ログ機能
from typing import List, Optional  # 型ヒント

# Pandocが利用可能か事前にチェック
try:
    # pypandoc が Pandoc を見つけられるか試す
    pypandoc.get_pandoc_version()
    print("Pandoc が見つかりました。")
except OSError:
    print("Pandoc が見つかりません。自動インストールを試みます...")
    try:
        # pypandoc を使用してPandocを自動インストール
        pypandoc.download_pandoc()
        print("Pandoc を自動インストールしました。")
    except Exception as e:
        print(f"Pandoc の自動インストールに失敗しました: {e}")
        # GUIを起動する前にエラーを表示
        root = tk.Tk()
        root.withdraw()  # メインウィンドウを隠す
        messagebox.showerror("エラー", 
            "Pandocが見つかりません。\n\n以下の方法でPandocをインストールしてください：\n"
            "1. https://pandoc.org/installing.html からダウンロード\n"
            "2. または PowerShell で: choco install pandoc\n"
            "3. または: winget install --id JohnMacFarlane.Pandoc")
        root.destroy()
        exit()

# エンコーディング問題を解決するためのヘルパー関数
def preprocess_rtf_file(rtf_path: str) -> str:
    """
    RTFファイルのエンコーディング問題と構造問題を修正するための前処理
    """
    import tempfile
    import codecs
    
    try:
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rtf', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
            
            # 元のファイルを複数のエンコーディングで試行
            encodings = ['utf-8', 'cp1252', 'latin1', 'shift_jis', 'utf-16', 'cp932']
            content = None
            
            for encoding in encodings:
                try:
                    with open(rtf_path, 'r', encoding=encoding, errors='replace') as source:
                        content = source.read()
                        break
                except UnicodeDecodeError:
                    continue
            
            # どのエンコーディングでも読めない場合、バイナリで読んで強制変換
            if content is None:
                with open(rtf_path, 'rb') as source:
                    raw_content = source.read()
                    content = raw_content.decode('utf-8', errors='replace')
            
            # RTFの構造を修復
            content = fix_rtf_structure(content)
            
            temp_file.write(content)
            return temp_path
                
    except Exception as e:
        print(f"前処理エラー: {e}")
        # 前処理が失敗した場合は元のファイルを返す
        return rtf_path

def fix_rtf_structure(content: str) -> str:
    """
    RTFファイルの構造的な問題を修復する
    """
    try:
        # RTFヘッダーが正しく開始されているかチェック
        if not content.strip().startswith('{\\rtf'):
            # RTFヘッダーが見つからない場合、簡単なRTFとしてラップ
            content = '{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}} ' + content + '}'
        
        # 不完全な括弧を修正
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if open_braces > close_braces:
            # 閉じ括弧が不足している場合、追加
            content += '}' * (open_braces - close_braces)
        elif close_braces > open_braces:
            # 開き括弧が不足している場合、先頭に追加
            content = '{' * (close_braces - open_braces) + content
        
        # 不正な制御文字を削除
        import re
        # NULL文字やその他の問題のある文字を削除
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', content)
        
        # RTFファイルが正しく終了していることを確認
        if not content.rstrip().endswith('}'):
            content += '}'
        
        return content
        
    except Exception as e:
        print(f"RTF構造修復エラー: {e}")
        return content

def create_encoding_filter() -> str:
    """
    Pandoc用のエンコーディング修正フィルターのパスを返す
    実際にはフィルターファイルは作成せず、空文字列を返す
    """
    return ""

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

            # RTFファイルのエンコーディング問題を解決するため、複数の方法を試行
            conversion_successful = False
            
            # 方法1: 標準的な変換
            try:
                pypandoc.convert_file(
                    rtf_path,
                    'markdown_strict',
                    format='rtf',
                    outputfile=output_md_path,
                    extra_args=['--wrap=none']
                )
                results_log_text.insert(tk.END, f"  -> 成功: {output_md_path} に保存しました。\n\n")
                success_count += 1
                conversion_successful = True
            except Exception as first_error:
                results_log_text.insert(tk.END, f"  -> 標準変換失敗、前処理を実行中...\n")
                
                # 方法2: ファイルを前処理してから変換
                try:
                    preprocessed_file = preprocess_rtf_file(rtf_path)
                    pypandoc.convert_file(
                        preprocessed_file,
                        'markdown_strict',
                        format='rtf',
                        outputfile=output_md_path,
                        extra_args=['--wrap=none']
                    )
                    # 一時ファイルを削除                    if preprocessed_file != rtf_path and os.path.exists(preprocessed_file):
                        os.remove(preprocessed_file)
                    results_log_text.insert(tk.END, f"  -> 成功（前処理後）: {output_md_path} に保存しました。\n\n")
                    success_count += 1
                    conversion_successful = True
                except Exception as second_error:
                    results_log_text.insert(tk.END, f"  -> 前処理変換も失敗、別の方法を試行中...\n")
                    
                    # 方法3: RTFをプレーンテキストに変換してからMarkdownに
                    try:
                        # プレーンテキストとして変換
                        text_content = pypandoc.convert_file(
                            rtf_path,
                            'plain',
                            format='rtf',
                            extra_args=['--wrap=none']
                        )
                        
                        # プレーンテキストからMarkdownに変換
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as txt_file:
                            txt_file.write(text_content)
                            txt_path = txt_file.name
                        
                        pypandoc.convert_file(
                            txt_path,
                            'markdown_strict',
                            format='plain',
                            outputfile=output_md_path,
                            extra_args=['--wrap=none']
                        )
                        
                        # 一時ファイルを削除
                        if os.path.exists(txt_path):
                            os.remove(txt_path)
                            
                        results_log_text.insert(tk.END, f"  -> 成功（プレーンテキスト経由）: {output_md_path} に保存しました。\n\n")
                        success_count += 1
                        conversion_successful = True
                        
                    except Exception as third_error:
                        error_msg = f"全ての変換方法が失敗: {str(third_error)}\n推奨: RTFファイルを別のソフトでDOCX形式に変換してから再試行してください。"
                        results_log_text.insert(tk.END, f"  -> 失敗: {error_msg}\n\n")
                        failure_count += 1
            
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