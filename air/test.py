from algorithm import Template
import cv2
from settings import Settings as ST
path_creen = r"C:\Users\Admin\Desktop\matching\air\test\template_screen.png"
path_key =r"C:\Users\Admin\Desktop\matching\air\test\template_search.png"


ST.CVSTRATEGY = ['orb','akaze','brisk'] # hàng đợi thuật toán, chạy lần lượt trái qua phải, dừng khi có ngưỡng lớn hơn thiết lập


# def convertImageToBox(path, )
a = Template(path_key,threshold=0.5,rgb=True)
result = a.match_all_in(path_creen)  # lấy toàn bộ object có trong creen, đưa trực tiếp đường dẫn screen vào png
print(result)
result = a.match_in(path_creen) # lấy 1 object thỏa mãn lớn hơn ngưỡng, đưa trực tiếp dường dẫn creen vào dạng png
print(result)
# print("time :",result['time'])
# print("Confident rate ",result['confidence'])
# print(result["location"][1])
# print(result["location"][9])
# print(result)
