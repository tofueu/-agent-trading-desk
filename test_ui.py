import sys

def test_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    print("Checking HTML structure...")

    # 1. Navigation tabs check
    assert 'tabAiCenter' in content, "Missing tabAiCenter ID"
    assert 'tabTrading' in content, "Missing tabTrading ID"
    assert 'switchView' in content, "Missing switchView JS function"
    print("✓ Navigation tabs structure verified")

    # 2. View panels check
    assert 'id="viewAiCenter"' in content, "Missing viewAiCenter panel"
    assert 'id="viewTradingConsole"' in content, "Missing viewTradingConsole panel"
    print("✓ View panels verified")

    # 3. AI Agents & Humans check
    assert 'GPT-4o' in content, "Missing GPT-4o model"
    assert 'Claude 3.5' in content, "Missing Claude model"
    assert 'Gemini 1.5' in content, "Missing Gemini model"
    assert 'DeepSeek V3' in content, "Missing DeepSeek model"
    assert '未連接 API' in content or '未連線 API' in content, "Missing unconnected API status"
    print("✓ AI Models & Humans roster verified")

    # 4. Project Categories check
    assert '金融交易量化模型' in content, "Missing trading project"
    assert '全棧 Web 控制台' in content, "Missing dev project"
    assert 'AI 行銷內容生成' in content, "Missing content project"
    assert '用戶行為數據分析' in content, "Missing analysis project"
    assert '多 Agent 協同研究' in content, "Missing research project"
    print("✓ 5 Project categories verified")

    # 5. Task Queue & Form check
    assert 'id="dispatchForm"' in content, "Missing task dispatch form"
    assert 'id="aiTaskList"' in content, "Missing task list container"
    assert 'handleDispatchTask' in content, "Missing handleDispatchTask JS function"
    assert 'onclick="completeTask' not in content, "Found inline completeTask onclick attribute - expected safe addEventListener"
    print("✓ Task Queue & safe dispatch system verified")

    # 6. Activity log check
    assert 'id="aiEvents"' in content, "Missing AI events log"
    assert 'logAi' in content, "Missing logAi JS function"
    print("✓ Activity log verified")

    # 7. Preserved Trading Console check
    assert 'Balance / ETH' in content, "Missing original Trading balance panel"
    assert 'Tail Probability Ridge' in content, "Missing original Trading Ridge graph"
    assert 'Handoff Chord' in content, "Missing original Trading Chord graph"
    assert '5D Strategy Lattice' in content, "Missing original Trading Lattice graph"
    print("✓ Preserved original trading console verified")

    print("\nALL UI STRUCTURE CHECKS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_html()
