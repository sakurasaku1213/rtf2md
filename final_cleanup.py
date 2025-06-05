#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys

def clean_final_output(text):
    """最終出力をクリーンアップ"""
    print("最終出力をクリーンアップ中...")
    
    lines = text.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        
        # 空行はスキップ
        if not line:
            continue
            
        # テーブル幅指定の残骸（x4535, x9070など）を除去
        if re.match(r'^x\d+$', line):
            continue
            
        # その他の制御コード残骸を除去
        if re.match(r'^[a-z]\d+$', line):
            continue
            
        # 非常に短い行で、数字と記号のみの行を除去
        if len(line) <= 3 and re.match(r'^[\d\W]+$', line):
            continue
            
        clean_lines.append(line)
    
    result = '\n'.join(clean_lines)
    
    # 複数の連続する空行を1つにまとめる
    result = re.sub(r'\n\s*\n+', '\n\n', result)
    
    print(f"最終クリーンアップ完了: {len(clean_lines)} 行を保持")
    return result.strip()

def apply_final_cleanup(input_file, output_file):
    """既存の変換結果に最終クリーンアップを適用"""
    print(f"最終クリーンアップを適用: {input_file}")
    
    try:
        # 既存のファイルを読み込み
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"読み込み完了: {len(content)} 文字")
        
        # 最終クリーンアップを適用
        cleaned_content = clean_final_output(content)
        
        # 結果をプレビュー
        print("\n--- 最終クリーンアップ後のプレビュー（最初の1000文字）---")
        preview = cleaned_content[:1000]
        print(preview)
        print("--- プレビュー終了 ---\n")
        
        # 新しいファイルに保存
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"最終クリーンアップ完了: {output_file}")
        print(f"出力ファイルサイズ: {len(cleaned_content)} 文字")
        
        return True
        
    except Exception as e:
        print(f"最終クリーンアップエラー: {e}")
        return False

def main():
    """メイン処理"""
    if len(sys.argv) != 2:
        print("使用方法: python final_cleanup.py <入力ファイル>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    # 出力ファイル名を生成（_final_converted.mdを_cleaned.mdに変更）
    if input_file.endswith("_final_converted.md"):
        output_file = input_file.replace("_final_converted.md", "_cleaned.md")
    else:
        output_file = input_file.replace(".md", "_cleaned.md")
    
    if not os.path.exists(input_file):
        print(f"エラー: 入力ファイルが見つかりません: {input_file}")
        sys.exit(1)
    
    print("=== 最終クリーンアップ処理 ===")
    
    if apply_final_cleanup(input_file, output_file):
        print(f"✓ 最終クリーンアップ成功: {output_file}")
        
        # ワークスペースにもコピー
        workspace_output = r"e:\rtftomd\WLJP_Hanrei_converted_clean.md"
        try:
            import shutil
            shutil.copy2(output_file, workspace_output)
            print(f"✓ ワークスペースにコピー: {workspace_output}")
        except Exception as e:
            print(f"ワークスペースへのコピーに失敗: {e}")
    else:
        print("✗ 最終クリーンアップ失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()
