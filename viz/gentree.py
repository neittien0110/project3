# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Thuật toán được phát triển bởi
#     Bùi Đức Chế, 20183694, https://github.com/buiducche/project3
#     Nguyễn Đức Tiến, https://github.com/neittien0110
#  Syntax:
#         cd viz
#         python ./gentree.py
#  Output ../assets/*.png
#  Log:
#      - Tăng tốc độ bằng cách hiệu chỉnh file đầu vào csv một lần, rồi áp dụng cho 
#        thuật toán phía sau
#      - Giải đệ qui bằng vòng lặp lan theo chiều rộng. 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from enum import Enum
import random
from numpy import NAN
import pandas as pd
import graphviz
import os
import json
from infix_prefix import ExpressionConverter  
''' Hàm chuyển đổi biểu thức trung tố --> hậu tố'''

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# create a url variable that is the website link that needs to crawl
BASE_URL = 'http://sis.hust.edu.vn/ModuleProgram/CourseLists.aspx'   

#Thư mục chứa file đâu vào
COURSE_COLLECTION_FOLDER = "assets"
#Thư mục chứa file đâu ra
OUTPUT_FOLDER = COURSE_COLLECTION_FOLDER + "/graph2"

lineColors=["blue","orange","red","green","pink","#34084D","#00539B","#183b0b","#93585e"];

MAX_DEPENDANCY = 100
COMMON_NAME = "so many"

GRAPH_TYPE = 2
''' Kiểu xuất đồ thị '''

def spliit(ss):
    """_summary_
        Chuẩn hóa cú pháp của phòng đào tạo thành cú pháp riêng.
    Args:
        ss (_type_): _description_
    Returns:
        _type_: _description_
    """    
    if ss.find("OR") != -1 or ss.find("AND") != -1:
        ss = ss.replace("AND", ",").replace("OR", "/")
    if ss.find("(") != -1:
        subss = []
        sps = ""
        tick = 0;
        seq = ""
        check = False
        for i in range(len(ss)):
            if check == True:
                if ss[i] == "," or ss[i] == "/":
                    seq = seq + ss[i]
                check = False
            else:
                if (tick == 1 and ss[i] == ")") or (tick == 0 and ss[i] == "("):
                    if sps != "":
                        subss.append(sps)
                        check = True
                    sps = sps + ss[i]
                    sps = ""
                else:
                    if (tick == 0 and (ss[i] == "," or ss[i] == "/")):
                        subss.append(sps)
                        seq = seq + ss[i]
                        sps = ""
                    else:
                        sps = sps + ss[i]
            if ss[i] == "(": tick += 1
            if ss[i] == ")": tick -= 1
        if sps != "": subss.append(sps)
        data = ""
        seqposition = 0
        for sub in subss:
            subrp = sub.replace(",", "AND").replace("/", "OR")
            data = data + subrp
            if seqposition != len(seq): data = data + seq[seqposition]
            seqposition = seqposition + 1
        return data
    else:
        return ss

def FindFullCourse(courseId):
    ''' Tìm cấu trúc chứa thông tin đầy đủ về một mã học phần nào đó'''
    global standardizedCourses; 
    for x in standardizedCourses:
        if x['X']==courseId:
            return x  
    return 0 

def getDependent(courseId):
    """_summary_
        Lấy danh sách các học phần phụ thuộc
    Args:
        courseId (_type_): học phần muốn tìm kiếm
    Returns:
        _type_: danh sách các học phần phụ thuộc
    """
    for myCourse in standardizedCourses:
        if courseId == myCourse['X']:
            return myCourse['Y']
    return ""

def Operator2NodeStyle(operator):
    if operator == ",":
        return NodeStyle.And
    elif operator == "/":
        return NodeStyle.Or

#----------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------
def findDependant(HP, dot, setHP):
    """_summary_
        Tìm kiếm các môn học bị phụ thuộc vào môn hiện thời.
        Thuật giải quét chiều rộng, không đệ qui.
    Args:
        HP (_type_): Mã học phần cần tìm. Ví dụ IT3030
        dot (_type_): handler điều khiển graphviz
        setHP (set): tập hợp chứa các cạnh phụ thuộc
    """    


    # Hàng đợi cần tìm kiếm phụ thuộc
    dependant_queue = []
    # Danh sách các học phần đã xử lý xong. Loại bỏ khỏi dependant_queue thì tống vào đây
    scaned_queue = []
    
    # Đưa học phần đầu tiên vào danh sách cần tìm kiếm
    dependant_queue.append(HP)
    RegisterAndRenderNode(dot, HP, NodeStyle.Root)

    '''Phụ trách phân tích biểu thức phụ thuộc'''
    EC = ExpressionConverter(); '''Phụ trách phân tích biểu thức phụ thuộc'''
    '''Phụ trách phân tích biểu thức phụ thuộc'''

    #Giới hạn số lượt quét học phần phụ thuộc
    limited = 0;

    #Quét toàn bộ danh sách các học phần cần tìm phụ thuộc
    while len(dependant_queue)>0 :
        #Lấy ra học phần gốc để tìm kiếm phụ thuộc
        victim = dependant_queue.pop();
        if victim in scaned_queue:
            continue
        scaned_queue.append(victim)
        
        #text mô tả sự phụ thuộc của sis
        dependentText = getDependent(victim)
        if (dependentText == ''): continue
        
        #Phân tích text chứa thông tin học phần theo kiểu của sis
        dependentTopo = EC.infixtodict(dependentText)
        
        #Top của cấu trúc phụ thuộc đương nhiên là học phần gốc rồi.
        parent_queue = []
        parent_queue.append(victim)
        parent_queue.append(dependentTopo)
        
        while (len(parent_queue)>0):       
            childrenTopo = parent_queue.pop()
            parent = parent_queue.pop()
            #Nếu có toán tử, thì ngay lập tức tạo node trung gian
            if (childrenTopo.__contains__("operator")):
                # Tạo node trung chuyển 
                switch_name = RegisterAndRenderNode(dot, str(childrenTopo).__hash__(), Operator2NodeStyle(childrenTopo['operator']))
                # Lựa chọn 1 màu để tô cho các cạnh
                edge_color = random.choice(lineColors)
                # Tạo 1 cạnh liền duy nhất, nối trực tiếp giữa học phần đang xử lý và điểm trung chuyển
                dot.edge(parent, switch_name, style="solid", color=edge_color )
                # chuyển parent thành điểm trung gian toán tư luôn
                parent = switch_name
                
            #Kết nối với các toán hạng đang có
            if (childrenTopo.__contains__("operands")):
                children = childrenTopo["operands"]
            elif type(childrenTopo) == str:
                children = [childrenTopo]
            else:
                children = childrenTopo
            for operand in children:
                # Đăng kí ngay để quét tiếp            
                if type(operand) == dict:
                    parent_queue.append(parent);
                    parent_queue.append(operand);
                else:
                    # Tạo node phụ thuộc
                    RegisterAndRenderNode(dot, operand, NodeStyle.Dependency)
                    # Và tạo 1 cạnh liền duy nhất, nối trực tiếp giữa học phần đang xử lý và học phần phụ thuộc duy nhất
                    dot.edge(parent, operand, style="solid", color=random.choice(lineColors))                    
                    dependant_queue.append(operand);                    
        # Hết lệnh if
    # Kết thúc vòng lặp duyệt tất cả các phần tử dependant_queue
    return
#----------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------
def findCaller(HP, dot, setHP):
    """_summary_
        Tìm kiếm các môn học bị phụ thuộc vào môn hiện thời
    Args:
        HP (_type_): Mã học phần cần tìm. Ví dụ IT3030
        dot (_type_): handler điều khiển graphviz
        setHP (set): tập hợp chứa các cạnh phụ thuộc
    """    

    # Hàng đợi cần tìm kiếm phụ thuộc
    caller_queue = []
    
    # Đưa học phần đầu tiên vào danh sách cần tìm kiếm
    caller_queue.append(HP)

    #Giới hạn số lượt quét học phần phụ thuộc
    limited = 0;
    
    #Quét toàn bộ danh sách các học phần cần tìm phụ thuộc
    while len(caller_queue)>0 :
        #Lấy ra học phần gốc để tìm kiếm học phần triệu gọi
        victim = caller_queue.pop();
        
        for myCourse in standardizedCourses:
            # Tìm xem học phần này có môn nào phụ thuộc không
            pos = str(myCourse['Y']).find(victim)
            if pos < 0 :
                continue
            if (limited > MAX_DEPENDANCY):
                Caller = COMMON_NAME
            else:    
                Caller = myCourse['X']
    
            # Điều kiện dừng đệ qui: khi học phần đã có trong danh sách cạnh
            if Caller in setHP:
               continue
            else:
               setHP.add(Caller);
                       
            #Nếu có môn phụ thuộc, lại kiểm tra xem môn đó là phụ thuộc 100%, hay là OR.
            halfCaller = False;
            if (pos>0 and myCourse['Y'][pos-1] == "/"):   
                halfCaller = True      
            if (pos < len(myCourse['Y'])-1 and myCourse['Y'][pos+1] == "/"):   
                halfCaller = True 

            # Tạo node caller và..
            RegisterAndRenderNode(dot, Caller, NodeStyle.Caller)   
            
            # .. và vẽ thêm cạnh nối vào đồ thị.
            # Vẽ nét đứt nếu bị lệ thuộc một phần (do điều kiện hoặc), và nét liền nếu lệ thuộc hoàn toàn (điều kiện and)
            if halfCaller:
                dot.edge(Caller, victim, style="dotted")
            else: 
                dot.edge(Caller, victim)  
                
            
            # Mở rộng danh sách cần đệ qui 
            if (limited <= MAX_DEPENDANCY):
                limited = limited + 1
                caller_queue.append(Caller);
        # Kết thúc vòng lặp tìm xem có môn học nào phụ thuộc vào myCourse không?           
    return
    

class NodeStyle(Enum):
    ''' Các loại node để vẽ đồ thị'''
    Root = 0
    Caller =1
    CallerCluster =2
    Dependency = -1
    DependencyCluster = -2
    And = 9000          #Mã 9xxx dành cho các node tượng trưng/node switch phân cạnh, không phải học phần
    Or =  9001


ScannedNodes = []
''' Danh sách các node đã tồn tại'''

def RegisterAndRenderNode(dot, courseId, style : NodeStyle):
    """_summary_
        Vẽ thông tin node lên đồ thị 
    Args:
        dot (Graphviz):   Đối tượng quản lý đồ thị Graphviz. Do tính đệ qui của đồ thị nên dot có thể là một vùng con.
        courseId (string): Mã học phần. Ví dụ IT1110.
        style (NodeStyle): kiểu hiển thị. Đối với kiểu And, Or thì courseId sẽ dặt lại thành courseId_And, courseId_Or
    """   
        
    if (style == NodeStyle.CallerCluster or style == NodeStyle.DependencyCluster):
        myCourse = 0
    else:
        myCourse = FindFullCourse(courseId)
        
    graphNodeId = courseId
    '''Tên định danh của node trong cấu trúc đồ thị Graphviz'''
    
    # Trường hợp là node của học phần gốc cần tính toán
    if (style == NodeStyle.Root):
        dot.attr('node', shape='record', color='red:orange', style='filled', gradientangle='270', fontcolor='white', fontsize="18", fontname="Tahoma")
    # Trường hợp là node của học phần bị phụ thuộc vào học phần hiện tại
    if (style == NodeStyle.Caller):
        dot.attr('node', shape='record', color='#ff000042', style='filled', fontcolor='black', fontsize="14", fontname="Tahoma")
        pass
    # Trường hợp là node của học phần điều kiện
    if (style == NodeStyle.Dependency):
        dot.attr('node', shape='record', color='lightblue', style='filled', fontcolor='black', fontsize="14", fontname="Tahoma")
        pass
    # Trường hợp là node của học phần điều kiện
    if (style == NodeStyle.And or style == NodeStyle.Or):
        dot.attr('node', shape='circle', color='gray', style='', fontcolor='darkgreen', fontsize="10", fontname="Tahoma")
        pass
    #-------------------------------------------------------------
    if style == NodeStyle.And:
        graphNodeId = str(courseId) + "_And"
        if not graphNodeId in ScannedNodes:
            dot.node(graphNodeId, label="và")
        ScannedNodes.append(graphNodeId)
    elif style == NodeStyle.Or:
        graphNodeId = str(courseId) + "_Or"
        if not graphNodeId in ScannedNodes:
            dot.node(graphNodeId, label="hoặc")
        ScannedNodes.append(graphNodeId)
    else:
        try: 
            graphNodeId = myCourse['Mã học phần']
            dot.node(graphNodeId, label="{" + "{id} | {name}  | {condition} | {credit}".format(
            id = myCourse['Mã học phần'],
            name=myCourse['Tên học phần'],
            condition = myCourse['Học phần điều kiện'],
            credit=myCourse['Thời lượng'] + " / " + str(myCourse['TC học phí']) + "đ / " + str(myCourse['Trọng số'])  ,
            ) + "}")       
            ScannedNodes.append(graphNodeId)   
        except:
            # Ghi nhận lỗi với node có tên là "so many"
            print ("Không vẽ được với " + str(courseId))                    
    return graphNodeId
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Main program
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import graphviz

import csv

  


#Chuyển đổi đường dẫn tương đối thành tuyệt đối
COURSE_COLLECTION_FOLDER = os.getcwd() + '/../' + COURSE_COLLECTION_FOLDER
OUTPUT_FOLDER = os.getcwd() + '/../' +  OUTPUT_FOLDER

csvfile = open(COURSE_COLLECTION_FOLDER + '/CourseListdata.csv', 'r',encoding="utf-8-sig")
'''File dữ liệu đầu vào, kết quả của quá trình crawl dữ liệu trang sis'''
#csvfile = open("E:\StProjects/2020-2021\BuiDucChe_CrawlVaVeCayPhuThuocHocPhan\sources/assets/CourseListdata.csv", 'r',encoding="utf-8")

reader = csv.DictReader(csvfile)

standardizedCourses = []; 
''' Danh sách đầy đủ các course với thông tin đã được chuẩn hoá.'''

#Bố trí lại thông tin phụ thuộc
for myCourse in reader:
    dk=str(myCourse['Học phần điều kiện']);
    dependency=dk.replace("*", "").replace("=", "").replace(" ", "").replace("!", "")
    
    myCourse['X']= myCourse['Mã học phần'] #Mã học phần chính, trùng lặp dữ liệu để tiện cho thuật toán tìm quan hệ
    myCourse['Y']= dependency       #Mã học phần điều kiện, trùng lặp dữ liệu để tiện cho thuật toán tìm quan hệ
    #if len(dependency) > 60:
    #    print(myCourse)
    standardizedCourses.append(myCourse)
#print(standardizedCourses[12]['HP']);


setHP = set()
courseIndex = 0
for myCourse in standardizedCourses:
    courseIndex  = courseIndex + 1;
    
    if not ((myCourse['X'] == 'CH3225') or (myCourse['X'] == 'BF3010')
            or (myCourse['X'] == 'BF4321') or (myCourse['X']=='CH4714')
            or (myCourse['X'] == 'CH3306') or (myCourse['X']=='EV3121')
            or (myCourse['X'] == 'EV4113') or (myCourse['X']=='IT4653')
            or (myCourse['X'] == 'CH5700') or (myCourse['X']=='EE3510')) :
        continue        
    #if courseIndex < 2520: 
    #    continue
    #if (myCourse['X'] != 'CH3630'):
    #   continue        
                    
    setHP.clear();
    dot = graphviz.Digraph('G', 
                           node_attr={'shape': 'record',}, 
                           edge_attr={'len': '2.0'}
                           )
    # Nén: các node cluster sẽ lồng vào nhau
    dot.attr(compound='true')
    
    # Đưa nút gốc, mã học phần gốc vào, với màu sắc chỉ định
    # Tham khảo: https://graphviz.org/doc/info/shapes.html
    RegisterAndRenderNode(dot, myCourse['X'], style=NodeStyle.Root)   

    # Chuẩn hóa dữ liệu từ file csv
    print("Vẽ đồ thị: HP " + myCourse['X']+ " --dk--> " + myCourse['Y'])
    
    # Lần theo dấu vết các cạnh là các học phần phụ thuộc
    dot.attr('node', shape='box', color='white', style='filled', fontcolor='black')     # Không hiểu sao phải thiết lập thuộc tính ở đây, nếu không thì node đại diện cho cluster sẽ kông đổi atrribute được
    dot.edge_attr.update(arrowhead='none', arrowsize='1')
    ScannedNodes.clear()
    findDependant(myCourse["X"], dot, setHP)
    
    # Lần theo dấu vết các cạnh là các học phần cần môn này
    #dot.attr('node', shape='box', color='#ff000042', style='filled', fontcolor='black')    
    dot.edge_attr.update(arrowhead='inv', arrowsize='1',)
    findCaller(myCourse["X"], dot, setHP)
    
    #Vẽ đồ thị
    try:
        # format='svg'
        dot.render(OUTPUT_FOLDER + '/' + myCourse['X'], view=False,format='png')
    except:
        print("     error to export to file with {0}".format(myCourse['X']))
        pass    
    dot.clear()