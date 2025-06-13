import asyncio
from optimized_api_client import OptimizedBuffClient, OptimizedYoupinClient

async def quick_analysis():
    print("快速分析两个平台Hash格式...")
    
    # 获取小样本
    async with OptimizedBuffClient() as buff_client:
        buff_data = await buff_client.get_all_goods_safe(max_pages=1)
    
    print(f'获取Buff数据: {len(buff_data) if buff_data else 0}个')
    if buff_data and len(buff_data) > 0:
        print('Buff Hash样本:')
        for i, item in enumerate(buff_data[:5]):
            print(f'  {i+1}. {item.get("market_hash_name", "N/A")}')
    
    async with OptimizedYoupinClient() as youpin_client:
        youpin_data = await youpin_client.get_all_items_safe(max_pages=1)
    
    print(f'\n获取悠悠有品数据: {len(youpin_data) if youpin_data else 0}个')
    if youpin_data and len(youpin_data) > 0:
        print('悠悠有品 Hash样本:')
        for i, item in enumerate(youpin_data[:5]):
            print(f'  {i+1}. {item.get("commodityHashName", "N/A")}')
    
    # 检查匹配情况
    if buff_data and youpin_data:
        buff_hashes = {item.get("market_hash_name", "") for item in buff_data if item.get("market_hash_name")}
        youpin_hashes = {item.get("commodityHashName", "") for item in youpin_data if item.get("commodityHashName")}
        
        matches = buff_hashes & youpin_hashes
        print(f'\n匹配分析:')
        print(f'  Buff Hash: {len(buff_hashes)}个')
        print(f'  悠悠有品 Hash: {len(youpin_hashes)}个')
        print(f'  精确匹配: {len(matches)}个')
        
        if matches:
            print('匹配示例:')
            for match in list(matches)[:3]:
                print(f'    - {match}')

if __name__ == "__main__":
    asyncio.run(quick_analysis()) 