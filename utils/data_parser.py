import re
import time
import json
from bs4 import BeautifulSoup

class DataParser:
    @staticmethod
    def sanitize_amount(text):
        cleaned = re.sub(r'[^\d.]', '', text)
        return f"{float(cleaned or 0):.2f}"

    @staticmethod
    def parse_key_value(section, selector):
        data = {}
        if not section:
            return data
        
        for cell in section.select(selector):
            key_elem = cell.select_one('.weui-cell__bd p')
            value_elem = cell.select_one('.weui-cell__ft')
            
            if key_elem and value_elem:
                key = key_elem.get_text(strip=True)
                value = value_elem.get_text(strip=True)
                if "余额" in key:
                    value = DataParser.sanitize_amount(value)
                data[key] = value or "暂无"
        return data

    @classmethod
    def parse_index(cls, html):
        soup = BeautifulSoup(html, 'html.parser')
        return {
            "services": ["账单"],
            "quick_balance": cls.parse_key_value(soup, '.weui-cell')
        }

    @classmethod
    def parse_account(cls, html):
        soup = BeautifulSoup(html, 'html.parser')
        sections = soup.find_all('div', class_='weui-cells')
        return {
            "personal": cls.parse_key_value(sections[0] if sections else None, '.weui-cell'),
            "school": cls.parse_key_value(sections[1] if len(sections) > 1 else None, '.weui-cell')
        }

    @staticmethod
    def parse_bill_json(json_data):
        items = []
        for item in json_data.get("dtls", []):
            create_ts = item.get("createtime", 0) // 1000
            time_str = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(create_ts))
            amount = f"￥{abs(item.get('amount', 0)):.2f}"
            transaction_type = item.get("tradename", "未知交易")
            if shop := item.get("shopname"):
                transaction_type += f"（{shop}）"
            
            items.append({
                "time": time_str,
                "type": transaction_type,
                "amount": amount,
                "status": "交易成功" if item.get("status") == 2 else "交易失败"
            })
        return items
    
    @staticmethod
    def parse_xxt_notices(json_str):
        """解析学习通通知和作业列表JSON内容
        
        Args:
            json_str (str): 从学习通获取的通知列表JSON字符串
            
        Returns:
            list: 通知信息列表，每个通知包含标题、内容、发送时间、课程信息等
        """
        notices = []
        try:
            # 尝试解析JSON字符串
            data = json.loads(json_str)
            
            # 获取通知列表
            notice_list = data.get("notices", {}).get("list", [])
            
            for notice in notice_list:
                try:
                    notice_info = {
                        "title": notice.get("title", "未知标题"),
                        "content": notice.get("content", "").replace("\r", "<br>"),
                        # 不存储rtf_content，可能包含复杂对象导致递归错误
                        "send_time": notice.get("sendTime", ""),
                        "complete_time": notice.get("completeTime", ""),
                        "creator_name": notice.get("createrName", "未知发送者"),
                        "is_read": notice.get("isread", 0) == 1,
                        # 不直接存储原始attachment，而是提取需要的信息
                        "uuid": notice.get("uuid", ""),
                        "id_code": notice.get("idCode", ""),
                    }
                    
                    # 判断是否为作业通知
                    if "作业" in notice_info["title"] or notice_info["title"].startswith("作业:"):
                        notice_info["type"] = "作业"
                    else:
                        notice_info["type"] = "通知"
                    
                    # 提取课程信息
                    if "tag" in notice and notice["tag"].startswith("courseId"):
                        notice_info["course_id"] = notice["tag"].replace("courseId", "")
                    
                    # 提取作业URL
                    try:
                        attachment_str = notice.get("attachment", "[]")
                        # 安全处理JSON字符串，避免解析错误
                        if isinstance(attachment_str, str):
                            attachment = json.loads(attachment_str)
                        else:
                            attachment = attachment_str
                            
                        if isinstance(attachment, list):
                            for item in attachment:
                                if isinstance(item, dict) and item.get("attachmentType") == 25 and "att_web" in item:
                                    web_info = item["att_web"]
                                    notice_info["work_id"] = web_info.get("examOrWorkId", "")
                                    notice_info["work_type"] = web_info.get("examOrWork", "")
                                    notice_info["class_id"] = web_info.get("clazzId", "")
                                    notice_info["course_id"] = web_info.get("courseId", "")
                                    notice_info["work_url"] = web_info.get("url", "")
                                    break
                    except Exception as e:
                        print(f"解析附件失败: {str(e)}")
                        # 继续处理，不影响通知的基本信息
                    
                    notices.append(notice_info)
                except Exception as e:
                    print(f"解析单个通知出错: {str(e)}")
                    continue
            
            return notices
            
        except Exception as e:
            print(f"解析学习通通知列表失败: {str(e)}")
            return []
    
    @staticmethod
    def parse_xxt_courses(html_content):
        """解析学习通课程列表HTML内容
        
        Args:
            html_content (str): 从学习通获取的课程列表HTML
            
        Returns:
            list: 课程信息列表，每个课程包含名称、学校、教师、开课时间和课程链接等信息
        """
        courses = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找所有课程块，包括正常课程和已结束课程
            course_divs = soup.find_all('div', class_='course')
            
            # 检查是否存在isState节点（已结束课程）
            is_state_div = soup.find('div', id='isState')
            if is_state_div:
                # 从isState节点获取结束课程
                ended_courses = is_state_div.find_all('div', class_='course')
                if ended_courses:
                    course_divs.extend(ended_courses)
            
            for course in course_divs:
                try:
                    course_info = {}
                    
                    # 提取课程信息
                    info_div = course.find('div', class_='course-info')
                    if not info_div:
                        continue
                    
                    # 获取课程ID和班级ID
                    clazz_id_input = course.find('input', {'name': 'clazzId'})
                    course_id_input = course.find('input', {'name': 'courseId'})
                    person_id_input = course.find('input', {'class': 'curPersonId'})
                    
                    if clazz_id_input and course_id_input:
                        course_info['clazz_id'] = clazz_id_input.get('value', '')
                        course_info['course_id'] = course_id_input.get('value', '')
                    
                    if person_id_input:
                        course_info['person_id'] = person_id_input.get('value', '')
                    
                    # 获取课程名称
                    course_name_span = info_div.find('span', class_='course-name')
                    if course_name_span:
                        # 优先获取title属性，其次获取文本内容
                        course_info['name'] = course_name_span.get('title', '') or course_name_span.text.strip()
                    else:
                        course_info['name'] = '未知课程'
                    
                    # 获取学校名称
                    school_p = info_div.find('p', class_='margint10')
                    if school_p:
                        course_info['school'] = school_p.get('title', '') or school_p.text.strip()
                    else:
                        # 尝试从第一个段落获取学校信息
                        all_p = info_div.find_all('p')
                        if all_p and len(all_p) > 0:
                            for p in all_p:
                                # 如果不是教师或时间信息，可能是学校信息
                                p_text = p.text.strip()
                                if not p.has_attr('class') or 'line2 color3' not in p.get('class', []):
                                    if not p_text.startswith('开课时间'):
                                        course_info['school'] = p.get('title', '') or p_text
                                        break
                        
                        # 如果仍然没有找到学校信息
                        if 'school' not in course_info:
                            course_info['school'] = '未知学校'
                    
                    # 获取教师名称
                    teacher_p = info_div.find('p', class_='line2 color3')
                    if teacher_p:
                        course_info['teacher'] = teacher_p.get('title', '') or teacher_p.text.strip()
                    else:
                        # 尝试查找任何可能包含教师信息的段落
                        teacher_p_list = info_div.find_all('p', class_='line2')
                        if teacher_p_list and len(teacher_p_list) > 1:
                            course_info['teacher'] = teacher_p_list[1].get('title', '') or teacher_p_list[1].text.strip()
                        else:
                            course_info['teacher'] = '未知教师'
                    
                    # 获取开课时间
                    time_found = False
                    time_p = info_div.find_all('p')
                    for p in time_p:
                        text = p.text.strip()
                        if "开课时间" in text:
                            course_info['time'] = text
                            time_found = True
                            break
                        
                    if not time_found:
                        course_info['time'] = '无开课时间信息'
                    
                    # 获取课程链接
                    course_link_a = info_div.find('a', class_='color1')
                    if course_link_a and 'href' in course_link_a.attrs:
                        course_info['link'] = course_link_a['href']
                    else:
                        course_info['link'] = ''
                    
                    # 获取课程图片
                    img_tag = course.find('img')
                    if img_tag and 'src' in img_tag.attrs:
                        course_info['image'] = img_tag['src']
                    else:
                        course_info['image'] = ''
                    
                    # 检查课程是否已结束
                    not_open_tip = course.find('a', class_='not-open-tip')
                    if not_open_tip:
                        course_info['status'] = not_open_tip.text.strip()
                    else:
                        course_info['status'] = '正常'
                    
                    courses.append(course_info)
                except Exception as e:
                    print(f"解析单个课程出错: {str(e)}")
                    continue
                    
            return courses
        except Exception as e:
            print(f"解析学习通课程列表失败: {str(e)}")
            return []