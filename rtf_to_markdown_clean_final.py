#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys

def decode_unicode_escape_final(text):
    """RTF内のUnicodeエスケープシーケンス（\\uXXXXX?）をデコードする（最終版）"""
    print(f"Unicode デコード開始: {len(text)} 文字")
    
    unicode_matches = []
    
    def replace_unicode_escape(match):
        try:
            unicode_num = int(match.group(1))
            if unicode_num < 0:
                unicode_num += 65536  # 負数の場合の処理
            char = chr(unicode_num)
            unicode_matches.append((match.group(0), char, unicode_num))
            return char
        except (ValueError, OverflowError):
            return match.group(0)  # 変換できない場合は元のまま
    
    # Unicodeエスケープパターンをマッチ（? も含めて除去）
    pattern = r'\\u(-?\d+)\\?\?'  # \u12345\? と \u12345? の両方に対応
    
    result_text = re.sub(pattern, replace_unicode_escape, text)
    
    # マッチした内容をプレビュー
    if unicode_matches:
        print(f"変換されたUnicodeエスケープ（最初の20個）:")
        for i, (original, decoded, num) in enumerate(unicode_matches[:20]):
            print(f"  {original} -> {decoded} (U+{num:04X})")
    
    print(f"Unicode デコード完了: 合計 {len(unicode_matches)} 個のエスケープを変換")
    return result_text

def clean_text_thoroughly(text):
    """テキストを徹底的にクリーンアップ"""
    print("テキストの徹底クリーンアップを開始...")
    
    lines = text.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 日本語文字（ひらがな、カタカナ、漢字）または英数字を含む行のみ
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u0030-\u0039\u0041-\u005A\u0061-\u007A]', line):
            
            # バイナリ残骸を除去
            # 連続する英字と数字だけの行（フォント名など）は除外
            if re.match(r'^[a-zA-Z\d\s;,&\-\.]+$', line) and len(line) > 50:
                continue
                
            # PNGやXMPデータの残骸を除去
            if any(keyword in line.lower() for keyword in ['png', 'idat', 'iend', 'ihdr', 'xml', 'xmp', 'adobe', 'rdf', 'width', 'height']):
                continue
                
            # RTF制御コードの残骸を除去
            if re.search(r'\\[a-z]+\d*', line):
                continue
                
            # 特殊文字を含む行（バイナリ残骸の可能性）をフィルタ
            if re.search(r'[^\u0020-\u007E\u3000-\u9FFF\uFF00-\uFFEF\s]', line):
                continue
                
            # フォント関連の行を除去
            if any(keyword in line for keyword in ['font', 'Helvetica', 'Arial', 'Times', 'Courier', 'Symbol']):
                continue
                
            # 短すぎる行（1-2文字）は除外（ただし日本語の場合は保持）
            if len(line) < 3 and not re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', line):
                continue
                
            clean_lines.append(line)
    
    print(f"クリーンアップ完了: {len(clean_lines)} 行を保持")
    return '\n'.join(clean_lines)

def extract_text_from_rtf_final(content):
    """RTFファイルから実際のテキスト内容を抽出（最終版）"""
    print(f"RTFテキスト抽出開始: {len(content)} 文字")
    
    try:
        # 1. RTFヘッダー情報とフォント定義を除去
        print("RTFヘッダー情報を除去中...")
        content = re.sub(r'\{\\fonttbl.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\colortbl.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\stylesheet.*?\}', '', content, flags=re.DOTALL)
        content = re.sub(r'\{\\info.*?\}', '', content, flags=re.DOTALL)
        
        # 2. バイナリデータ（画像など）を除去
        print("バイナリデータを除去中...")
        content = re.sub(r'\\pngblip.*?}', '', content, flags=re.DOTALL)
        content = re.sub(r'PNG.*?IEND.*?B`\\?', '', content, flags=re.DOTALL)
        content = re.sub(r'<\?xpacket.*?\?>', '', content, flags=re.DOTALL)
        content = re.sub(r'<x:xmpmeta.*?</x:xmpmeta>', '', content, flags=re.DOTALL)
        content = re.sub(r'<rdf:RDF.*?</rdf:RDF>', '', content, flags=re.DOTALL)
        
        # 3. Unicodeエスケープシーケンスをデコード
        print("Unicodeエスケープシーケンスをデコード中...")
        content = decode_unicode_escape_final(content)
        
        # 4. RTF制御コードを削除
        print("RTF制御コードを処理中...")
        content = re.sub(r'\\par\b', '\n', content)  # 段落区切り
        content = re.sub(r'\\line\b', '\n', content)  # 改行
        content = re.sub(r'\\tab\b', '\t', content)  # タブ
        
        # テーブル関連のコードを除去
        content = re.sub(r'\\intbl', '', content)
        content = re.sub(r'\\cell', '\t', content)
        content = re.sub(r'\\row', '\n', content)
        content = re.sub(r'\\trowd.*?(?=\\)', '', content)
        content = re.sub(r'\\clpad[lrtb]\d*', '', content)
        content = re.sub(r'\\clw[a-zA-Z]*\d*', '', content)
        content = re.sub(r'\\cellx\d+', '', content)
        
        # その他のRTF制御コードを削除
        content = re.sub(r'\\[a-z]+\d*\s?', '', content)
        content = re.sub(r'\\[^a-z\s]', '', content)
        
        # 残った波括弧を削除
        content = re.sub(r'[{}]', '', content)
        
        # 5. テキストを徹底的にクリーンアップ
        content = clean_text_thoroughly(content)
        
        # 6. 複数の空行を1つにまとめる
        content = re.sub(r'\n\s*\n+', '\n\n', content)
        
        print(f"最終テキスト: {len(content)} 文字")
        return content.strip()
        
    except Exception as e:
        print(f"テキスト抽出エラー: {e}")
        return content

def convert_rtf_to_markdown_final(rtf_path, output_path=None):
    """RTFファイルをMarkdownに変換（最終版）"""
    print(f"RTF変換開始: {rtf_path}")
    
    try:
        # 出力パスが指定されていない場合は自動生成
        if output_path is None:
            output_path = os.path.splitext(rtf_path)[0] + "_final_converted.md"
        
        print(f"出力先: {output_path}")
        
        # RTFファイルを読み込み
        content = None
        encodings = ['utf-8', 'cp1252', 'latin1', 'shift_jis', 'cp932']
        
        for encoding in encodings:
            try:
                with open(rtf_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                print(f"成功: {encoding} エンコーディングで読み込み完了")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if content is None:
            with open(rtf_path, 'rb') as f:
                raw_content = f.read()
                content = raw_content.decode('utf-8', errors='replace')
        
        print(f"読み込み完了: {len(content)} 文字")
        
        # RTFからテキストを抽出
        extracted_text = extract_text_from_rtf_final(content)
        
        # 抽出されたテキストをプレビュー
        print("\n--- 抽出されたテキストプレビュー（最初の1000文字）---")
        text_preview = extracted_text[:1000]
        print(text_preview)
        print("--- 抽出テキストプレビュー終了 ---\n")
        
        # Markdownファイルに保存
        print("Markdownファイルに保存中...")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        print(f"変換完了: {output_path}")
        print(f"出力ファイルサイズ: {len(extracted_text)} 文字")
        
        return True, f"変換成功: {output_path}"
        
    except Exception as e:
        print(f"変換エラー: {str(e)}")
        return False, f"変換エラー: {str(e)}"

def main():
    """メイン処理"""
    import argparse
    
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(
        description='RTFファイルをMarkdownに変換します',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python rtf_to_markdown_clean_final.py input.rtf
  python rtf_to_markdown_clean_final.py input.rtf -o output.md
  python rtf_to_markdown_clean_final.py "C:/Documents/file.rtf"
        """
    )
    
    parser.add_argument('input_file', help='変換するRTFファイルのパス')
    parser.add_argument('-o', '--output', help='出力するMarkdownファイルのパス（省略時は自動生成）')
    parser.add_argument('-q', '--quiet', action='store_true', help='詳細出力を抑制する')
    
    args = parser.parse_args()
    
    # 入力ファイルの存在確認
    rtf_file = args.input_file
    if not os.path.exists(rtf_file):
        print(f"エラー: RTFファイルが見つかりません: {rtf_file}")
        sys.exit(1)
    
    # 出力ファイルパスの設定
    output_file = args.output
    
    if not args.quiet:
        print("=== RTF to Markdown 変換 (最終版) ===")
        print(f"入力ファイル: {rtf_file}")
        if output_file:
            print(f"出力ファイル: {output_file}")
    
    success, message = convert_rtf_to_markdown_final(rtf_file, output_file)
    
    if success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
