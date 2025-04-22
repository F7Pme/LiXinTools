class DisplayHandler:
    @staticmethod
    def show_index(account_data):
        print("\n【个人信息】")
        print(f"姓名: {account_data['personal'].get('姓名', '未知')}")
        print(f"学工号: {account_data['personal'].get('学工号', '未知')}")
        print(f"账户余额: ￥{account_data['personal'].get('账户余额', '0.00')}")
        
        print("\n【学业信息】")
        print(f"学校: {account_data['school'].get('学校', '未知')}")
        print(f"专业: {account_data['school'].get('专业', '未设置')}")
        print(f"班级: {account_data['school'].get('班级', '未分配')}")
        
        print("\n【可用服务】")
        print("1. 账单查询")
        print("2. 电费查询")

    @staticmethod
    def show_bill(items, page_no, total_page):
        if not items:
            print(f"\n第 {page_no} 页无账单记录")
            return
        
        print(f"\n【第 {page_no} 页账单（共 {total_page} 页）】")
        for idx, item in enumerate(items, 1):
            print(f"{idx}. {item['time']} | {item['type']} | {item['amount']} | {item['status']}")