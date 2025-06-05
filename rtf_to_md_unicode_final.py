#!/usr/bin/env python3
"""
RTF to Markdown 変換スクリプト (Unicode対応・最終版)
日本語のUnicodeエスケープシーケンス（\\uXXXX\\?）を正しくデコードします。

使用方法:
    python rtf_to_md_unicode_final.py input_file.rtf [output_file.md]
"""

import sys
import os
import re
import argparse

def decode_unicode_escape(text):
    """RTF内のUnicodeエスケープシーケンス（\\uXXXX\\?）をデコードする"""
    def replace_unicode_escape(match):
        try:
            unicode_num = int(match.group(1))
            if unicode_num < 0:
                unicode_num += 65536  # 負数の場合の処理
            return chr(unicode_num)
        except (ValueError, OverflowError):
            return match.group(0)  # 変換できない場合は元のまま
    
    # \uXXXX\? パターンをマッチしてデコード（バックスラッシュ1つ）
    pattern = r'\\u(-?\d+)\\?'
    return re.sub(pattern, replace_unicode_escape, text)

def remove_images_and_objects(content):
    """RTFから画像とオブジェクトを完全に除去"""
    
    # {\pict ...} ブロックを除去（画像埋め込み）
    content = re.sub(r'\{\\pict[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', content, flags=re.DOTALL)
    
    # {\object ...} ブロックを除去（オブジェクト埋め込み）
    content = re.sub(r'\{\\object[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', content, flags=re.DOTALL)
    
    # {\*\shppict ...} ブロックを除去（Shape Picture）
    content = re.sub(r'\{\\\*\\shppict[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', content, flags=re.DOTALL)
    
    # PNG/JPEG/GIF などの画像データマーカーを除去
    content = re.sub(r'\\pngblip.*?(?=\\|$)', '', content, flags=re.DOTALL)
    content = re.sub(r'\\jpegblip.*?(?=\\|$)', '', content, flags=re.DOTALL)
    content = re.sub(r'\\wmetafile.*?(?=\\|$)', '', content, flags=re.DOTALL)
    
    # Base64やHex形式のデータブロックを除去
    content = re.sub(r'[a-fA-F0-9]{50,}', '', content)  # 長い16進数文字列
    content = re.sub(r'[A-Za-z0-9+/]{100,}=*', '', content)  # Base64っぽい長い文字列
    
    # PNGファイルシグネチャとその周辺を除去
    content = re.sub(r'PNG.*?IEND', '', content, flags=re.DOTALL)
    
    return content

def extract_text_from_rtf(content):
    """RTFファイルから実際のテキスト内容を抽出"""
    try:
        # まず画像とオブジェクトを除去
        content = remove_images_and_objects(content)
        
        # RTFヘッダー情報とフォント定義を除去
        content = re.sub(r'\{\\fonttbl.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\colortbl.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\stylesheet.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\info.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\generator.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\pntxtb.*?\}', '', content, flags=re.DOTALL)
        
        # Unicodeエスケープシーケンスをデコード（RTF制御コード除去前に実行）
        content = decode_unicode_escape(content)
        
        # RTF制御コードを削除（ただし段落マークは改行に変換）
        content = re.sub(r'\\par\b', '\n', content)  # 段落区切り
        content = re.sub(r'\\line\b', '\n', content)  # 改行
        content = re.sub(r'\\tab\b', '\t', content)  # タブ
        content = re.sub(r'\\page\b', '\n--- 改ページ ---\n', content)  # 改ページ
        
        # フォント制御コードを削除
        content = re.sub(r'\\f\d+\s?', '', content)  # フォント指定
        content = re.sub(r'\\fs\d+\s?', '', content)  # フォントサイズ
        content = re.sub(r'\\b\d*\s?', '', content)  # 太字
        content = re.sub(r'\\i\d*\s?', '', content)  # イタリック
        content = re.sub(r'\\ul\d*\s?', '', content)  # 下線
        
        # 色指定を削除
        content = re.sub(r'\\cf\d+\s?', '', content)  # 文字色
        content = re.sub(r'\\cb\d+\s?', '', content)  # 背景色
        
        # レイアウト関連の制御コードを削除
        content = re.sub(r'\\li\d+\s?', '', content)  # 左インデント
        content = re.sub(r'\\ri\d+\s?', '', content)  # 右インデント
        content = re.sub(r'\\sb\d+\s?', '', content)  # 段落前スペース
        content = re.sub(r'\\sa\d+\s?', '', content)  # 段落後スペース
        
        # テーブル関連の制御コードを削除
        content = re.sub(r'\\trowd.*?\\row', '', content, flags=re.DOTALL)
        content = re.sub(r'\\intbl', '', content)
        content = re.sub(r'\\cell', ' ', content)
        
        # その他のRTF制御コードを削除
        content = re.sub(r'\\[a-z]+\d*\s?', '', content)
        content = re.sub(r'\\[^a-z\s]', '', content)
        
        # 残った波括弧を削除
        content = re.sub(r'[{}]', '', content)
        
        # 不要な文字列を除去
        content = re.sub(r'Width\d+', '', content)  # Width4535 などを除去
        content = re.sub(r'ntbl', '', content)  # 不明な制御文字列を除去
        
        # 複数の空行を1つにまとめる
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        # 空白の正規化
        content = re.sub(r'[ \t]+', ' ', content)  # 複数のスペース・タブを1つに
        content = re.sub(r' *\n *', '\n', content)  # 行末・行頭の空白を削除
        
        # 意味のない短い行を除去
        lines = content.split('\n')
        filtered_lines = []
        for line in lines:
            line = line.strip()
            # 2文字未満の行や数字だけの行は除外（ただし、日本語文字が含まれている場合は保持）
            if (len(line) >= 2 and not line.isdigit()) or re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', line):
                filtered_lines.append(line)
        
        content = '\n'.join(filtered_lines)
        
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
        
        # RTFファイルを読み込み（latin1エンコーディングを優先使用）
        content = None
        encodings = ['latin1', 'utf-8', 'cp1252', 'shift_jis', 'cp932']
        
        for encoding in encodings:
            try:
                with open(rtf_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                print(f"エンコーディング {encoding} で読み込み成功")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # すべてのエンコーディングで失敗した場合はバイナリモードで読み込み
        if content is None:
            print("バイナリモードで読み込み中...")
            with open(rtf_path, 'rb') as f:
                raw_content = f.read()
                content = raw_content.decode('latin1', errors='replace')
        
        print(f"RTFファイルサイズ: {len(content)} 文字")
        
        # RTFからテキストを抽出
        extracted_text = extract_text_from_rtf(content)
        
        print(f"抽出されたテキストサイズ: {len(extracted_text)} 文字")
        
        # Markdownファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        print(f"変換完了: {output_path}")
        
        # 結果の概要を表示
        lines = extracted_text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        japanese_lines = [line for line in non_empty_lines if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', line)]
        print(f"行数: {len(lines)} (空行を除く: {len(non_empty_lines)}, 日本語含有行: {len(japanese_lines)})")
        
        if japanese_lines:
            print("日本語文例:")
            for line in japanese_lines[:3]:
                print(f"  {line[:100]}...")
        
        return True, f"変換成功: {output_path}"
        
    except Exception as e:
        print(f"変換エラー: {str(e)}")
        return False, f"変換エラー: {str(e)}"

def test_unicode_decoder():
    """Unicodeデコーダーのテスト"""
    test_samples = [
        "これは\\u12486\\?\\u12540\\?\\u12473\\?\\u12488\\?です。",
        "\\u26085\\?\\u26412\\?\\u35486\\?を\\u12486\\?\\u12467\\?\\u12540\\?\\u12489\\?しています。",
        "\\u20778\\?\\u25913\\?\\u20316\\?\\u25104\\?の\\u12486\\?\\u12461\\?\\u12473\\?\\u12488\\?です。"
    ]
    
    print("=== Unicodeデコーダーテスト ===")
    for i, sample in enumerate(test_samples, 1):
        print(f"\nテスト {i}:")
        print(f"入力: {sample}")
        decoded = decode_unicode_escape(sample)
        print(f"出力: {decoded}")

def main():
    parser = argparse.ArgumentParser(description='RTF to Markdown 変換ツール (Unicode対応・最終版)')
    parser.add_argument('input_file', nargs='?', help='入力RTFファイル')
    parser.add_argument('output_file', nargs='?', help='出力Markdownファイル（省略時は自動生成）')
    parser.add_argument('--test', action='store_true', help='Unicodeデコーダーのテストを実行')
    
    args = parser.parse_args()
    
    if args.test:
        test_unicode_decoder()
        return
    
    if not args.input_file:
        print("エラー: 入力ファイルを指定してください")
        parser.print_help()
        sys.exit(1)
    
    if not os.path.exists(args.input_file):
        print(f"エラー: ファイルが見つかりません: {args.input_file}")
        sys.exit(1)
    
    success, message = convert_rtf_to_markdown(args.input_file, args.output_file)
    
    if not success:
        print(f"変換に失敗しました: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
