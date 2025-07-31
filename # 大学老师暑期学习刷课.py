# 大学老师暑期学习刷课
from requests import options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, re 

def login(web, username, password):
    # 输入用户名和密码
    web.get("https://teacher.higher.smartedu.cn/h/subject/summer2025/")
    # 等待页面加载
    web.implicitly_wait(2)
    web.find_element(By.XPATH, '''//*[@id="loginHtml"]/div/div[1]/a''').click()
    iframes = web.find_elements(By.TAG_NAME, "iframe")
    # 等待 iframe 出现并切换
    web.switch_to.frame(iframes[0])
    WebDriverWait(web, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div[2]/label/div/input"))
    ).send_keys(username)
    WebDriverWait(web, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div[3]/label/div/input"))
    ).send_keys(password)  
    WebDriverWait(web, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div[5]/button/span"))
    ).click()


def get_class_list(web):
    # 等待课程列表加载
    try:
        web.get("https://teacher.higher.smartedu.cn/h/subject/summer2025/")
        WebDriverWait(web, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@class="news_content"]'))
        )
        
        courses = web.find_elements(By.XPATH, '//div[@class="news_content"]')
        news_times = web.find_elements(By.XPATH, '//div[@class="news_time"]')
        
        print("找到的课程数量:", len(courses))
        print("找到的课程时间:", len(news_times))
        
        need_learn_course_list = []
        for i, news_time in enumerate(news_times):  # 避免变量名 `time` 冲突
            time_text = news_time.text.strip()
            if time_text:
                # 使用正则表达式提取时间
                numbers = re.findall(r"\d+\.?\d*", time_text)
                print("匹配到的时间:", numbers)
                if float(numbers[2])-float(numbers[0])>0 : 
                    need_learn_course_list.append({"index":i, "time": float(numbers[2])-float(numbers[0])})
        
        print("课程时间列表:", need_learn_course_list)
        return need_learn_course_list
    except Exception as e:
        print("获取课程列表失败:", e)
        return []   


def start_learn(web, need_learn_list):
    for course in need_learn_list:
        index = course["index"]
        web.find_elements(By.XPATH, '//div[@class="news_content"]')[index].click()
        time.sleep(2)
        tabs = web.window_handles
        # Switch to the second tab
        web.switch_to.window(tabs[1])
        WebDriverWait(web, 10).until(
            EC.presence_of_element_located((By.ID, 'startStudy'))
        ).click()
        time.sleep(12)
        WebDriverWait(web, 15).until(
            EC.presence_of_element_located((By.ID, 'guideKnow'))
        ).click()
        print(f"开始学习课程 {index + 1}")
        #等待视频元素加载并准备就绪
        video = WebDriverWait(web, 30).until(
            lambda d: d.execute_script("return document.querySelector('video')")
        )
        # 等待视频元数据加载
        WebDriverWait(web,30).until(
            lambda d: d.execute_script("return arguments[0].readyState > 0 ", video)
        )
        time_start = time.time()
        print(f"开始学习：{ time.asctime(time.localtime(time.time()))}. 课程预计学习时间: {int(course['time']*3600)}秒(无倍速播放情况下)")

        while True:
            try:
                # 获取视频元素和总时长
                video = web.execute_script("return document.querySelector('video')")
                duration = web.execute_script("return arguments[0].duration", video)
                print(f"视频总时长: {duration:.1f}秒", end = "")
                # 获取当前播放时间
                current_time = web.execute_script("return arguments[0].currentTime", video)
                # 判断是否接近结束（最后1分钟）
                if duration - current_time <= 60:  # 最后60秒
                    web.execute_script("arguments[0].playbackRate = 2.0;", video)
                else:
                    #好像设置成10倍没有实际效果。
                    web.execute_script("arguments[0].playbackRate = 2.0;", video)
                
                web.execute_script("arguments[0].muted = true;", video)
                
                # 检查是否有弹窗按钮
                try:
                    button = WebDriverWait(web, 1).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@class="layui-layer-btn"]/a'))
                    )
                    if button: 
                        button.click()
                except:
                    pass
                
                time_gap = time.time() - time_start
                print("\r", time.asctime(time.localtime(time.time())), 
                      f"课程学习时间: {int(time_gap)}秒, 视频进度: {current_time:6.1f}/{duration:6.1f}秒", 
                      end="")
                
                if time_gap >= course["time"] * 2000:
                    print(f"\r课程 {index + 1} 学习完成，耗时 {time_gap:6.1f} 秒")
                    web.close() 
                    web.switch_to.window(tabs[0])
                    break
                    
                time.sleep(20)
                
            except Exception as e:
                print(f"\n发生错误: {str(e)}")
                web.close()
                web.switch_to.window(tabs[0])
                break


def main():
    # 设置 Chrome 浏览器选项
    options = Options()
    # options.add_argument("--headless")  # 无头模式
    options.add_argument("--disable-gpu")  # 禁用 GPU 加速
    options.add_argument("--no-sandbox")  # 禁用沙盒模式
    options.add_argument("--disable-dev-shm-usage")  # 禁用 /dev/shm 使用
    options.add_argument("--window-size=1920,1080")  # 设置窗口大小
    options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
    options.add_argument('--ignore-ssl-errors')         # 忽略 SSL 错误
    
    # 创建 Chrome 浏览器实例
    web = webdriver.Chrome(service=Service(), options=options)
    login(web, "your_username", "your_password")
    time.sleep(2)  # 等待登录完成
    need_learn_list = get_class_list(web)
    print(need_learn_list)
    start_learn(web, need_learn_list)
    
if __name__ == "__main__":
    main()
