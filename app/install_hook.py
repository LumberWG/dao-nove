"""安装 git pre-commit hook"""
import os, stat

CONTENT = r"""#!/bin/sh
echo ""
echo "📋 《岁蚀》提交前检查..."
STAGED=$(git diff --cached --name-only --diff-filter=ACM | grep -E 'chapters/新_第.*章_.*\.md$' || true)
if [ -z "$STAGED" ]; then
    echo "✅ 无章节文件变更，跳过检查"
    exit 0
fi
echo "   检查文件:"
for f in $STAGED; do echo "   - $f"; done
CHECKER="app/consistency_check.py"
if [ -f "$CHECKER" ]; then
    python "$CHECKER" $STAGED
    RESULT=$?
    if [ $RESULT -ne 0 ]; then
        echo ""
        echo "⚠️  发现问题！修复后重新 git add + git commit"
        echo "   强制提交: git commit --no-verify"
        exit 1
    fi
fi
echo ""
exit 0
"""

path = r'f:/Study/dao-nove/.git/hooks/pre-commit'
with open(path, 'w', newline='\n') as f:
    f.write(CONTENT)
os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
print(f"pre-commit hook installed: {path}")
