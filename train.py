from ultralytics import YOLO

def main():
    # Tải mô hình YOLOv8 Nano cấu hình sẵn
    model = YOLO("yolov8n.pt") 

    # Tiến hành Train bằng GPU
    model.train(
        data="data.yaml",   # Chỉ đến file data.yaml chung thư mục
        epochs=100,         # Số lượt huấn luyện (có thể sửa thành 50 nếu muốn chạy thử cho nhanh)
        imgsz=640,          # Kích thước ảnh đầu vào tiêu chuẩn
        batch=16,           # Số lượng ảnh xử lý cùng lúc (nếu báo lỗi Out of Memory thì giảm xuống 8)
        device=0            # Bắt buộc: Chạy bằng GPU đầu tiên của máy
    )

if __name__ == '__main__':
    main()