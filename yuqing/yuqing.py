#!/usr/bin/env python
# -*- coding: utf-8 -*-

#抓取bbs数据返回结果


import requests
import json
import sys  
from urllib import quote
from requests_toolbelt import MultipartEncoder
reload(sys)  
sys.setdefaultencoding('utf8')
import datetime
import time
import arrow
import os


def cc98Login(username,password):
    """
    登录cc98
    """
    posturl = "https://openid.cc98.org/connect/token"
    PayloadData = {
        "client_id"  : "9a1fd200-8687-44b1-4c20-08d50a96e5cd",
        "client_secret":"8b53f727-08e2-4509-8857-e34bf92b27f2",
        "username"   : username,
        "password"   : password,
        "grant_type" : "password",
        "scope":"cc98-api openid offline_access"
    }

    PayloadHeader = {
        "content-type": "application/x-www-form-urlencoded"
    }
    r = requests.post(posturl, data=PayloadData,headers=PayloadHeader)

    response_json = json.loads(r.text)

    authorization = "Bearer " + response_json["access_token"]
    return authorization



def getTotalInform(username,password,date):
    """
    按照关键词进行匹配，词表维护在data里面
    """
    total_list = list()
    url = "https://api.cc98.org/topic/search?keyword={}&size=20&from=0"
    authorization = cc98Login(username, password)
    headers = {"authorization":authorization}
    with open('data') as file:
        for line in file.readlines():
            keyword = line.strip()
            format_url = url.format(quote(keyword))
            response_json = json.loads(requests.get(format_url,headers=headers).text)
            total_list += response_json
            print("get the search word " + keyword + "result" )
            time.sleep(10)
    print("search finish , wait data process")
    MessageProcess(total_list,date)
            
def getContentInform(id):
    """
    获取帖子的内容
    """

    url = "https://api.cc98.org/Topic/{}/post?from=0&size=10"
    format_url = url.format(id)
    authorization = cc98Login(username, password)
    headers = {"authorization":authorization}
    response_json = json.loads(requests.get(format_url,headers=headers).text)
    return response_json[0].get("content")


    
def MessageProcess(response_list,date_input):
    """
    消息处理（时间、发布人信息、title、内容 =》excel）
    """
    file_w = open("result.xls",'w')
    for items in  response_list :
        date = items.get("time", "")
        if arrow.get(date).year == int(date_input.split("-")[0]) \
        and arrow.get(date).month == int(date_input.split("-")[1]) :
        # and arrow.get(date).day == int(date_input.split("-")[-1]):
            status    = "0"
            userId    = items.get("userId", "")
            username  = items.get("userName") if items.get("userName") is not None else ""  
            title     = items.get("title") if items.get("title") is not None else ""
            id        = items.get("id")
            url       = "https://www.cc98.org/topic/{}".format(id)
            boardName = items.get("boardName")
            hitcount  = items.get("hitCount")
            reply     = items.get("replyCount") 
            content   = getContentInform(id).replace('\n', '').replace('\r', '') if getContentInform(id) is not None else ""
            lacResult = UseBaiduLACAnalysis(title,content)
            time.sleep(1)
            print lacResult
            if analysis(content,title):
                status = "1"
            file_w.write(str(date)+'\t'+boardName +'\t'+ str(userId) + '\t'+ username + '\t'+ title +'\t'+ content+'\t'+status+'\t'+str(lacResult)+'\t'+str(reply)+'\t'+str(hitcount)+'\t'+url+'\n')

    file_w.close()
    os.system("iconv -f UTF8 -t GB18030 result.xls >result_new.xls")
    print("generate file")

def UseBaiduLACAnalysis(title,content):
    """
    用baidu开源的nlp接口来辅助判断
    """
    AK = "qxjHxdNaGqBxdWUMR98SBi2h"
    CK = "PmFr2k9OjitVi2EkG3G2wB2yK7WOHXSP"
    url = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}'
    headers = {"Content-Type":"application/json"}
    format_url = url.format(AK,CK)
    response_json = json.loads(requests.get(format_url,headers=headers).text)
    access_token = response_json.get("access_token")
    
    url = "https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify?charset=UTF-8&access_token={}"
    format_url = url.format(access_token)
    s = {"text":content}
    response_json = json.loads(requests.post(format_url,data=json.dumps(s),headers=headers).text)
    content_sentiment = response_json.get("items")[0].get("sentiment")
    time.sleep(0.5)
    s = {"text":title}
    response_json = json.loads(requests.post(format_url,data=json.dumps(s),headers=headers).text)
    title_sentiment = response_json.get("items")[0].get("sentiment")

    return min(content_sentiment,title_sentiment)






def analysis(title, content):
    with open("blacklist") as file :
        for line in file.readlines():
            blackword = line.strip()
            if blackword in title or blackword in content:
                return True
    return False


    


if __name__ == '__main__':
    date = input("date(yyyy-mm-dd):")
    username = input("username(cc98):")
    password = input("password(cc98 Login):")
    getTotalInform(username, password, date)
    print("Finish")

    





