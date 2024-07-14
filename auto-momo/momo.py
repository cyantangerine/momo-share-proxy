# encoding:utf-8
from asyncio import create_task, wait, Semaphore, run
from os import environ

from aiohttp import ClientSession, ClientTimeout

from ip import listIP, getheaders, ip_main

global n  # 记录访问成功次数
global error_count_dict

link = 'link'  # 设置link
with open("./url.txt", mode="r", encoding="utf-8") as f:
    link = f.readline()

# 如果检测到程序在 github actions 内运行，那么读取环境变量中的登录信息
if environ.get('GITHUB_RUN_ID', None) and 'link' in environ.keys():
    link = environ['link']


async def create_aiohttp(url, proxy_list):
    global n, error_count_dict
    n = 0
    error_count_dict = {
        "proxy_connect": 0,
        "timeout": 0,
        "proxy_internal": 0,
        "momo_connect": 0,
        "other": 0,
        "指定的网络名不再可用": 0,
        "信号灯超时时间已到": 0
    }
    print("开始尝试...")
    async with ClientSession(timeout=ClientTimeout(total=600)) as session:
        # 生成任务列表
        task = []
        count = 0
        for proxy in proxy_list:
            count += 1
            # if count == 100:
            #     break
            # print(f"创建任务...{proxy}")
            # web_request(url, proxy, session)
            task.append(create_task(web_request(url, proxy, session, count)))
        await wait(task)
        print("等待完毕")


# 网页访问
async def web_request(url, proxy, session, count):
    # 并发限制
    # print(f"request {proxy}")
    global error_count_dict
    async with Semaphore(5):
        try:
            async with await session.get(url=url, headers=await getheaders(), proxy=proxy,
                                         timeout=ClientTimeout(total=600, ceil_threshold=600)) as response:
                # 返回字符串形式的相应数据
                page_source = await response.text()
                await page(page_source)
                print(f"尝试成功...{proxy}")
            if count % 100 == 0:
                print(f"已完成 {count}，成功{n}，错误统计：{error_count_dict}")

        except Exception as e:
            if str(e):
                error_str = str(e)
                ipport = str(proxy).replace('http://', '').replace('https://', '')
                if error_str.find("host " + ipport) != -1 or error_str.find("Server disconnected") != -1:
                    error_count_dict["proxy_connect"] += 1
                elif error_str.find(f"URL('{proxy}')") != -1:
                    error_count_dict["proxy_internal"] += 1
                elif error_str.find(f"www.maimemo.com:443") != -1:
                    error_count_dict["momo_connect"] += 1
                elif error_str.find(f"指定的网络名不再可用") != -1:
                    error_count_dict["指定的网络名不再可用"] += 1
                elif error_str.find(f"信号灯超时时间已到") != -1:
                    error_count_dict["信号灯超时时间已到"] += 1
                else:
                    error_count_dict["other"] += 1
                    print(f"{proxy} Fail: {e}")
            else:
                error_count_dict["timeout"] += 1
                # print(f"{proxy} Fail TimeOut: {e}")
                # traceback.print_exc()

            pass


# 判断访问是否成功
async def page(page_source):
    global n, error_count_dict
    if "学习天数" in page_source:
        n += 1
    else:
        if "data_read_false" not in error_count_dict: error_count_dict["data_read_false"] = 0
        error_count_dict["data_read_false"] += 1


def main():
    global error_count_dict
    ip_list = ip_main()  # 抓取代理
    run(create_aiohttp(link, ip_list))

    res = f"总代理数量{len(ip_list)}，墨墨分享链接访问成功{n}次。错误统计：{error_count_dict}"
    print(res)
    with open("./time.log", mode="a", encoding="utf-8") as f:
        f.write("\n" + res + "\n")


if __name__ == '__main__':
    main()
