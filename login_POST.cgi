#!/usr/bin/python3
import sys
import os
from urllib.parse import parse_qs

#qString = os.environ['QUERY_STRING'] #GET방식은 CGI 환경변수로 데이터를 전달

qString = sys.stdin.readline() #POST 방식은 CGI 표준입력으로 데이터전달

qVal = parse_qs(qString)
name = qVal['name'][0]
passwd = qVal['passwd'][0]

responseBody = f'<HTML><HEAD><META charset="utf-8"></HEAD>'\
               f'<BODY><H1> Hello POST {name}'\
               f'<BR> Your password is {passwd} </H1><BR>'\
               f'<a href="index.html"> Home </a> <BR> </BODY></HTML>'

print(responseBody)



