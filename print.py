import win32api
import win32print

file_name = "C://Users//2023odagiri-PJ//Downloads//00000-3858912153.png"
try:
    win32api.ShellExecute(0, "print", file_name, "Microsoft Print to PDF", ".", 0)
    print("Printed:", file_name)
except Exception as e:
    print(f"印刷エラー: {str(e)}")