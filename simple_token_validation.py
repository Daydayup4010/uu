#!/usr/bin/env python3
"""简化的Token验证，避免子进程编码问题"""
import asyncio
from token_manager import TokenManager

async def validate_buff_token_simple():
    """简化的Buff Token验证"""
    try:
        tm = TokenManager()
        result = await tm.validate_buff_token(force_check=True)
        print(f"Buff Token验证结果: {result}")
        return result
    except Exception as e:
        print(f"Buff Token验证异常: {e}")
        return {"valid": False, "error": str(e), "cached": False}

async def validate_youpin_token_simple():
    """简化的悠悠有品Token验证"""
    try:
        tm = TokenManager()
        result = await tm.validate_youpin_token(force_check=True)
        print(f"悠悠有品Token验证结果: {result}")
        return result
    except Exception as e:
        print(f"悠悠有品Token验证异常: {e}")
        return {"valid": False, "error": str(e), "cached": False}

async def main():
    """主函数"""
    print("简化Token验证测试")
    print("=" * 30)
    
    print("1. 验证Buff Token...")
    buff_result = await validate_buff_token_simple()
    
    print("\n2. 验证悠悠有品Token...")
    youpin_result = await validate_youpin_token_simple()
    
    print("\n" + "=" * 30)
    print("验证结果总结:")
    print(f"Buff Token: {'有效' if buff_result.get('valid') else '无效'}")
    print(f"悠悠有品Token: {'有效' if youpin_result.get('valid') else '无效'}")
    
    if buff_result.get('valid') and not youpin_result.get('valid'):
        print("\n结论: 只有悠悠有品Token无效，Buff Token正常")
    elif not buff_result.get('valid') and not youpin_result.get('valid'):
        print("\n结论: 两个Token都无效")
    elif buff_result.get('valid') and youpin_result.get('valid'):
        print("\n结论: 两个Token都有效")
    else:
        print("\n结论: 只有Buff Token无效，悠悠有品Token正常")

if __name__ == "__main__":
    asyncio.run(main()) 