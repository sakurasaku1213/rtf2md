import re

def find_unicode_patterns(rtf_path):
    """RTFファイル内のUnicodeエスケープシーケンスの実際のパターンを見つける"""
    with open(rtf_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    print("Unicodeエスケープシーケンスのパターンを検索中...")
    
    # さまざまなパターンを試行
    patterns = [
        r'\\u\d+\\?',    # \u1234\ or \u1234
        r'\\u\d+\?',     # \u1234?
        r'\\u-?\d+\?',   # \u-1234? or \u1234?
        r'\\u-?\d+\\',   # \u-1234\ or \u1234\
        r'\\u\d+[?\\]?', # \u1234? or \u1234\ or \u1234
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        if matches:
            print(f"パターン '{pattern}' で {len(matches)} 個のマッチを発見:")
            # 最初の10個を表示
            for i, match in enumerate(matches[:10]):
                print(f"  {i+1}: {repr(match)}")
            if len(matches) > 10:
                print(f"  ... (他 {len(matches) - 10} 個)")
            print()
    
    # 特定のUnicodeエスケープ形式を手動で検索
    print("手動パターン検索:")
    sample_content = content[:10000]  # 最初の10,000文字をサンプルとして使用
    
    # \u で始まる部分を探す
    u_positions = []
    pos = 0
    while True:
        pos = sample_content.find('\\u', pos)
        if pos == -1:
            break
        # その後の20文字を表示
        context = sample_content[pos:pos+20]
        u_positions.append(context)
        pos += 1
    
    if u_positions:
        print(f"\\u で始まる文字列の例 ({len(u_positions)} 個発見):")
        for i, context in enumerate(u_positions[:10]):
            print(f"  {i+1}: {repr(context)}")
    else:
        print("\\u で始まる文字列が見つかりませんでした")

if __name__ == "__main__":
    rtf_file = r"C:\Users\yoshida\Desktop\アプリ倉庫\decoded_test.rtf"
    find_unicode_patterns(rtf_file)
