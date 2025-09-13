import tkinter as tk
from tkinter import scrolledtext
from tkinter import Checkbutton
from PIL import Image, ImageTk  #pillow库
from openai import OpenAI
from TTS import  BD_toapivoice as ss
import json
import os

con=["","","","","","","",""]
c=0
with open("config/config.txt",'r',encoding='utf-8') as conf:  #读取配置文件
    for line in conf:
        con[c]=line.strip('\n')
        c=c+1
cdata = 'data/'+con[2]
######################配置###################################
client = OpenAI(api_key=con[0], base_url="https://api.yuegle.com/v1") #输入api_key即可
filename = cdata     #存档文件路径
models = con[1]   #可选
stream = True
image1 = Image.open("image/image3.png")

log=1
messages = []       #创建格式列表

def Txt_Create():   #创建数据文件
    if os.path.isfile(filename):  #存在则跳过
        pass
    else:
        open(filename, 'w')  #没有则创建

def chat_list():#载入存档数据函数	
    result=[]
    a=0  #计行数
    h=0  #本次使用限制行数
    with open(filename,'r',encoding='utf-8') as f:  #读取数据行数
        for line in f:
            a=a+1
    with open(filename,'r',encoding='utf-8') as f:  #读取内容
        for line in f:
            h=h+1
            if(h>a-130):
                result.append(json.loads(line.strip('\n')))  #逐行读取
    dct='Y'         #input("是否继续存档数据（Y / N 默认为Y）：")
    if(dct=='Y' or not dct):
        return result
    global log
    log=0
    return []

Txt_Create()    #生成文件
messages = chat_list()   #延续数据

def run_ai(q):
    global messages
    messages.append({"role": "user", "content": q})  #多轮对话记忆
    try:  #尝试请求
        window.after(200, window.update())
        response = client.chat.completions.create(   #api请求生成
            model=models,
            messages=messages,
            stream=stream   #流式对话
        )
    except Exception as e:
        messages.pop()
        scr.insert('end',"错误信息："+str(e))
        messages = chat_list()
        return "erro"

    #write!no connect other
    if(log==1):
        data = {"role": "user", "content": q}
        string=json.dumps(data,ensure_ascii=False)  #dict转str格式，专用于json
        with open (filename,'a+',encoding='utf-8') as f:  #向日志中存入本次提问
            f.write(string)
            f.write('\n')
    m_answer=""

    #流式对话文本处理
    if stream:
        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            content = delta.content if delta and delta.content else ""
            content = content.replace("None", "")
            m_answer += content
            scr.insert('end', content)
            scr.see(tk.END)
            window.after(200, window.update())   #窗口更新

#非流式对话文本处理
    else:     
        strings=str(response.choices[0].message.content)  #转化格式
        strings=strings.replace("None", "")   #修复deepseekR1异常文本
        m_answer=strings   #非流式无需额外操作
        scr.insert('end',strings)   #文本框内容添加
        scr.see(tk.END)   #文本框底部自动换行
        window.after(200, window.update())   #窗口更新
	#多轮对话处理
    messages.append({"role": "assistant", "content": m_answer})     
	#存入对话数据
    if(log==1):         
        data = {"role": "assistant", "content": str(m_answer)}  #固定传入deepseek数据流格式
        string=json.dumps(data,ensure_ascii=False)#dict转str格式，专用于json
        with open (filename,'a+',encoding='utf-8') as f:  #向日志中存入本次回答
            f.write(string)
            f.write('\n')
    if CheckVar1.get()==1:
        ss.runapi(str(m_answer))
    #ss.toplay()

def on_submit():
    input_text = entry.get()  #获得输入信息
    entry.delete(0, tk.END)  # 清空输入框
    entry.insert(0,'wait...')
    scr.delete(1.0,'end')      #删除所有元素，刷新文本框
    a = "我："+input_text+"\n\n"
    scr.insert('end',a)  #在文本框中显示本次"我"的发言
    run_ai(input_text)  #按下后启动api请求
    entry.delete(0, tk.END)  # 清空输入框

# 创建主窗口
window = tk.Tk()
window.title("Yuchat")
window.iconbitmap("image/lightball.ico")
window.geometry("500x700")  # 设置窗口大小
window.attributes("-alpha", 0.95) #设置窗口透明度
window.attributes("-toolwindow", False) #设置窗口样式
window.attributes("-topmost", True) #设置窗口最前
window.resizable(0,0)

photo1 = ImageTk.PhotoImage(image1)  #加载背景文件
label1 = tk.Label(window, image=photo1)  #背景
label1.pack(fill=tk.BOTH, expand=tk.YES)  #图片自适应

#创建复选框
CheckVar1 = tk.IntVar()
CheckVar1.set(0)
check1 = Checkbutton(
    window,
    text="语音",
    bg="#DBDBDB",
    font=('黑体', 10,'bold'),
    variable = CheckVar1,
    onvalue=1,
    offvalue=0)
check1.place(relx=0.065, rely=0.04, anchor=tk.CENTER)

#创建文本框
scr = scrolledtext.ScrolledText(
	window,
	width=25,
	height=5,
    font=("黑体", 15),
    fg = "#000000",#前景色
    bg="#E4E1DC"
)
scr.place(relx=0.50, rely=0.12, anchor=tk.CENTER)

# 创建输入框
entry = tk.Entry(  
    window,
    width=30,
    bg="#D6D2D1",
    font=("黑体", 15)
)
entry.place(relx=0.50, rely=0.88, anchor=tk.CENTER)

# 创建提交按钮
submit_btn = tk.Button(
    window,
    text="^",
    command=on_submit,
    width=8,
    bg="#FFFFFF",
    fg="black",
    font=("黑体", 11)
)
submit_btn.place(relx=0.5, rely=0.92, anchor=tk.CENTER)

# 运行主循环
window.mainloop()
