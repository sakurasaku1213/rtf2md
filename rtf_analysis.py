import re
import tempfile

def decode_rtf_unicode(content):
    """RTFのUnicodeエスケープシーケンスをデコードする"""
    def replace_unicode(match):
        try:
            # \uXXXX\ の形式から数値を抽出
            unicode_value = int(match.group(1))
            # 負の値の場合は65536を足す（RTFの仕様）
            if unicode_value < 0:
                unicode_value += 65536
            # Unicode文字に変換
            return chr(unicode_value)
        except (ValueError, OverflowError):
            # 変換できない場合は元の文字列を返す
            return match.group(0)
    
    # \uXXXX\ パターンをデコード（RTFファイルの実際の形式）
    content = re.sub(r'\\u(\d+)\\', replace_unicode, content)
    return content

def analyze_rtf_file(rtf_path):
    """RTFファイルを分析し、構造上の問題を特定する"""
    try:
        with open(rtf_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        print(f"ファイル分析: {rtf_path}")
        print(f"総文字数: {len(content)}")
        print(f"Unicode エスケープ数: {content.count('\\u')}")
        
        # 括弧バランスをチェック
        open_braces = content.count('{')
        close_braces = content.count('}')
        print(f"開き括弧 {{: {open_braces}")
        print(f"閉じ括弧 }}: {close_braces}")
        print(f"括弧バランス: {'OK' if open_braces == close_braces else 'NG - 差: ' + str(open_braces - close_braces)}")
        
        # RTFヘッダーをチェック
        header_match = re.search(r'^\\{rtf\d+', content)
        print(f"RTFヘッダー: {'あり' if header_match else 'なし'}")
        
        # ファイルの最初と最後を表示
        print(f"\nファイル開始 (最初の200文字):")
        print(content[:200])
        print(f"\nファイル終了 (最後の200文字):")
        print(content[-200:])
        
        # 前処理後の内容もテスト
        print(f"\n--- 前処理テスト ---")
        decoded_content = decode_rtf_unicode(content)
        unicode_reduction = content.count('\\u') - decoded_content.count('\\u')
        print(f"デコードされたUnicodeエスケープ数: {unicode_reduction}")
        
        # デコード後のサンプルテキストを抽出
        sample_text = re.sub(r'\\[a-zA-Z]+\d*\s*', '', decoded_content[:1000])
        sample_text = re.sub(r'[{}]', '', sample_text).strip()
        if sample_text:
            print(f"デコード後テキストサンプル: {sample_text[:200]}...")
        
        return decoded_content
        
    except Exception as e:
        print(f"分析エラー: {e}")
        return None

if __name__ == "__main__":
    rtf_file = r"C:\Users\yoshida\Desktop\アプリ倉庫\decoded_test.rtf"
    analyze_rtf_file(rtf_file)
