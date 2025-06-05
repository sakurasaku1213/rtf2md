import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import re
import sys
import codecs

def decode_unicode_escape(text):
    """RTF内のUnicodeエスケープシーケンス（\\uXXXX?）をデコードする"""
    def replace_unicode_escape(match):
        try:
            unicode_num = int(match.group(1))
            if unicode_num < 0:
                unicode_num += 65536  # 負数の場合の処理
            return chr(unicode_num)
        except (ValueError, OverflowError):
            return match.group(0)  # 変換できない場合は元のまま
    
    # \uXXXX? パターンをマッチしてデコード
    pattern = r'\\u(-?\d+)\?'
    return re.sub(pattern, replace_unicode_escape, text)

def extract_text_from_rtf(content):
    """RTFファイルから実際のテキスト内容を抽出"""
    try:
        # RTFヘッダー情報とフォント定義を除去
        # {\fonttbl...} や {\colortbl...} などの定義を削除
        content = re.sub(r'\{\\fonttbl.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\colortbl.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\stylesheet.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\info.*?\}', '', content, flags=re.DOTALL)
        
        # RTF制御コードを削除（ただし段落マークは改行に変換）
        content = re.sub(r'\\par\b', '\n', content)  # 段落区切り
        content = re.sub(r'\\line\b', '\n', content)  # 改行
        content = re.sub(r'\\tab\b', '\t', content)  # タブ
        
        # その他のRTF制御コードを削除
        content = re.sub(r'\\[a-z]+\d*\s?', '', content)  # \fs24, \f0 など
        content = re.sub(r'\\[^a-z\s]', '', content)  # \', \\ など
        
        # 残った波括弧を削除
        content = re.sub(r'[{}]', '', content)
        
        # Unicodeエスケープシーケンスをデコード
        content = decode_unicode_escape(content)
        
        # 複数の空行を1つにまとめる
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()
        
    except Exception as e:
        print(f"テキスト抽出エラー: {e}")
        return content

def convert_rtf_to_markdown(rtf_path, output_path=None):
    """RTFファイルをMarkdownに変換（Unicode対応版）"""
    try:
        # 出力パスが指定されていない場合は自動生成
        if output_path is None:
            output_path = os.path.splitext(rtf_path)[0] + "_converted.md"
        
        # RTFファイルを読み込み（複数のエンコーディングを試行）
        content = None
        encodings = ['utf-8', 'cp1252', 'latin1', 'shift_jis', 'cp932']
        
        for encoding in encodings:
            try:
                with open(rtf_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # すべてのエンコーディングで失敗した場合はバイナリモードで読み込み
        if content is None:
            with open(rtf_path, 'rb') as f:
                raw_content = f.read()
                content = raw_content.decode('utf-8', errors='replace')
        
        # RTFからテキストを抽出
        extracted_text = extract_text_from_rtf(content)
        
        # Markdownファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        return True, f"変換成功: {output_path}"
        
    except Exception as e:
        return False, f"変換エラー: {str(e)}"

# グローバル変数
selected_rtf_filepaths = []

def select_rtf_files_action():
    """RTFファイル選択"""
    global selected_rtf_filepaths
    filepaths_tuple = filedialog.askopenfilenames(
        title="RTFファイルを選択 (複数選択可)",
        filetypes=(("RTFファイル", "*.rtf"), ("すべてのファイル", "*.*"))
    )
    if filepaths_tuple:
        selected_rtf_filepaths = list(filepaths_tuple)
        if len(selected_rtf_filepaths) > 3:
            display_files = ", ".join([os.path.basename(f) for f in selected_rtf_filepaths[:3]]) + f", 他 {len(selected_rtf_filepaths) - 3}件"
        else:
            display_files = ", ".join([os.path.basename(f) for f in selected_rtf_filepaths])
        selected_files_var.set(f"{len(selected_rtf_filepaths)} 個のファイルを選択: {display_files}")
    else:
        selected_rtf_filepaths = []
        selected_files_var.set("ファイルが選択されていません")

def convert_files_action():
    """ファイル変換処理"""
    global selected_rtf_filepaths
    if not selected_rtf_filepaths:
        messagebox.showwarning("ファイル未選択", "変換するRTFファイルを選択してください。")
        return

    results_log_text.config(state=tk.NORMAL)
    results_log_text.delete('1.0', tk.END)
    results_log_text.insert(tk.END, "変換処理を開始します...\n")

    success_count = 0
    failure_count = 0

    for rtf_path in selected_rtf_filepaths:
        output_md_path = os.path.splitext(rtf_path)[0] + "_unicode_converted.md"
        log_message_prefix = f"処理中: {os.path.basename(rtf_path)} -> {os.path.basename(output_md_path)}\n"
        results_log_text.insert(tk.END, log_message_prefix)
        root.update_idletasks()

        try:
            if not os.path.exists(rtf_path):
                raise FileNotFoundError("指定されたRTFファイルが見つかりません。")

            success, message = convert_rtf_to_markdown(rtf_path, output_md_path)
            
            if success:
                results_log_text.insert(tk.END, f"  -> 成功: {message}\n\n")
                success_count += 1
            else:
                results_log_text.insert(tk.END, f"  -> 失敗: {message}\n\n")
                failure_count += 1

        except Exception as e:
            results_log_text.insert(tk.END, f"  -> 失敗: {e}\n\n")
            failure_count += 1

        results_log_text.see(tk.END)
        root.update_idletasks()

    final_summary = f"\n--- 変換処理完了 ---\n成功: {success_count}件\n失敗: {failure_count}件\n"
    results_log_text.insert(tk.END, final_summary)
    results_log_text.config(state=tk.DISABLED)

    messagebox.showinfo("変換完了", f"処理が完了しました。\n成功: {success_count}件, 失敗: {failure_count}件\n詳細はログを確認してください。")
    selected_rtf_filepaths = []
    selected_files_var.set("ファイルが選択されていません")

def test_unicode_decoder():
    """Unicodeデコーダーのテスト"""
    test_window = tk.Toplevel(root)
    test_window.title("Unicodeデコーダーテスト")
    test_window.geometry("600x400")
    
    tk.Label(test_window, text="テスト用RTFテキスト（Unicodeエスケープ含む）:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=5)
    
    input_text = scrolledtext.ScrolledText(test_window, height=8, font=("Consolas", 9))
    input_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
      # サンプルテキストを挿入
    sample_text = r"""これは\\u12486?\\u12540?\\u12473?\\u12488?です。
\\u26085?\\u26412?\\u35486?を\\u12486?\\u12467?\\u12540?\\u12489?しています。
\\u20778?\\u25913?\\u20316?\\u25104?\\u12398?\\u12486?\\u12461?\\u12473?\\u12488?です。"""
    input_text.insert('1.0', sample_text)
    
    tk.Label(test_window, text="デコード結果:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10,5))
    
    output_text = scrolledtext.ScrolledText(test_window, height=8, font=("Arial", 9))
    output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def decode_test():
        input_content = input_text.get('1.0', tk.END).strip()
        decoded_content = decode_unicode_escape(input_content)
        output_text.delete('1.0', tk.END)
        output_text.insert('1.0', decoded_content)
    
    decode_button = tk.Button(test_window, text="デコード実行", command=decode_test, 
                             bg="#007bff", fg="white", font=("Arial", 9))
    decode_button.pack(pady=10)
    
    # 初回実行
    decode_test()

# --- GUI のセットアップ ---
root = tk.Tk()
root.title("RTF to Markdown 変換 (Unicode対応版)")
root.geometry("700x600")

# ファイル選択フレーム
file_frame = tk.Frame(root, padx=10, pady=10)
file_frame.pack(fill=tk.X)

tk.Label(file_frame, text="RTFファイル選択:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

select_button = tk.Button(file_frame, text="RTFファイルを選択", command=select_rtf_files_action, 
                         bg="#007bff", fg="white", font=("Arial", 9))
select_button.pack(anchor=tk.W, pady=(5, 10))

selected_files_var = tk.StringVar()
selected_files_var.set("ファイルが選択されていません")
selected_files_label = tk.Label(file_frame, textvariable=selected_files_var, 
                               wraplength=600, justify=tk.LEFT, font=("Arial", 9))
selected_files_label.pack(anchor=tk.W, fill=tk.X)

# 変換ボタンフレーム
convert_frame = tk.Frame(root, padx=10, pady=5)
convert_frame.pack(fill=tk.X)

convert_button = tk.Button(convert_frame, text="変換開始", command=convert_files_action, 
                          bg="#28a745", fg="white", font=("Arial", 10, "bold"))
convert_button.pack(side=tk.LEFT, padx=(0, 10))

test_button = tk.Button(convert_frame, text="Unicodeテスト", command=test_unicode_decoder, 
                       bg="#ffc107", fg="black", font=("Arial", 9))
test_button.pack(side=tk.LEFT)

# 結果表示フレーム
results_frame = tk.Frame(root, padx=10, pady=10)
results_frame.pack(fill=tk.BOTH, expand=True)

tk.Label(results_frame, text="変換結果ログ:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

results_log_text = scrolledtext.ScrolledText(results_frame, height=15, state=tk.DISABLED, 
                                            font=("Consolas", 9))
results_log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

# 使用説明
info_frame = tk.Frame(root, padx=10, pady=5)
info_frame.pack(fill=tk.X)

info_text = """使用方法:
1. 「RTFファイルを選択」でRTFファイルを選択
2. 「変換開始」で変換実行
3. 元のファイル名に「_unicode_converted.md」が付加されたMarkdownファイルが作成されます
4. 「Unicodeテスト」でUnicodeエスケープシーケンスのデコード機能を確認できます"""

tk.Label(info_frame, text=info_text, font=("Arial", 8), justify=tk.LEFT, 
         bg="#f8f9fa", relief=tk.RIDGE, padx=5, pady=5).pack(fill=tk.X)

# アプリ起動
if __name__ == "__main__":
    root.mainloop()
