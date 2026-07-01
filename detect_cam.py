import cv2
from ultralytics import YOLO
import serial
import time

# --- 1. CẤU HÌNH KẾT NỐI SERIAL VỚI ESP32 ---
SERIAL_PORT = 'COM7'
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1) # Giảm timeout để phản hồi nhanh
    time.sleep(2) 
    print(f"Đã kết nối thành công với Thùng rác ESP32 qua cổng {SERIAL_PORT}!")
except Exception as e:
    print(f"Lỗi kết nối Serial: {e}")
    ser = None

# --- 2. TẢI MÔ HÌNH YOLOV8 CỦA BẠN ---
model_path = r"D:\thungrackhon\runs\detect\train-6\weights\best.pt"
model = YOLO(model_path)
 # Sử dụng mô hình YOLOv8 nano để nhận diện nhanh hơn

# --- 3. MỞ WEBCAM LAPTOP ---
cap = cv2.VideoCapture(0)
win_name = "He Thong Phan Loai Rac IoT"
print("\nHệ thống AI đã sẵn sàng!")
print("Đang chờ tín hiệu DETECTED (Khoảng cách <= 10cm) từ ESP32...\n")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Không thể kết nối hoặc đọc dữ liệu từ Webcam!")
        break
        
    annotated_frame = frame.copy()
    current_frame_objects = []
    
    # --- 4. LẮNG NGHE TÍN HIỆU TỪ ESP32 ---
    if ser and ser.in_waiting > 0:
        try:
            raw_data = ser.readline()
            signal = raw_data.decode('utf-8', errors='ignore').strip()
            
            # Nếu khoảng cách bé hơn 10cm, ESP32 sẽ gửi chuỗi "DETECTED"
            if "DETECTED" in signal:
                print("\n" + "="*50)
                print("[CẢM BIẾN BÁO] Vật thể cách < 10cm! Chụp ảnh quét nhận diện...")
                
                # Đọc lại frame mới nhất để tránh trễ ảnh
                for _ in range(5): cap.read() 
                _, scan_frame = cap.read()
                
                # Đưa khung hình vào YOLO nhận diện
                results = model(scan_frame, show=False, verbose=False)
                best_label = None
                highest_conf = 0.0
                
                for result in results:
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        label = model.names[class_id]
                        conf = float(box.conf[0])
                        
                        if label != "person" and conf > 0.40:
                            if conf > highest_conf:
                                highest_conf = conf
                                best_label = label
                
                # --- 5. GỬI KẾT QUẢ PHÂN LOẠI TRỰC TIẾP VỀ CHO ESP32 ---
                if best_label:
                    print(f"-> Phát hiện rác: '{best_label}' ({highest_conf*100:.1f}%)")
                    
                    if best_label in ["plastic", "can"]:
                        print("=> Gửi mã '1' -> Khớp lệnh RÁC TÁI CHẾ xuống Servo.")
                        ser.write(b'1')
                        
                    elif best_label in ["Glass", "glass", "METAL", "Metal"]:
                        print("=> Gửi mã '3' -> Khớp lệnh RÁC VÔ CƠ xuống Servo.")
                        ser.write(b'3')
                        
                    else:
                        print("=> Nhãn khác -> Gửi mã '2' (Mặc định RÁC HỮU CƠ) xuống Servo.")
                        ser.write(b'2')
                else:
                    print("=> Không nhận diện được nhãn rõ ràng -> Gửi mã '2' (Mặc định RÁC HỮU CƠ).")
                    ser.write(b'2')
                print("="*50)
                
                # Ngủ ngắn để tránh đọc trùng dữ liệu cũ vòng lặp tiếp theo
                time.sleep(1)
                ser.reset_input_buffer()
                
        except Exception as serial_err:
            print(f"Lỗi đọc dữ liệu Serial: {serial_err}")

    # --- 6. HIỂN THỊ CAMERA LIVE VÀ VẼ KHUNG CHỮ ---
    results_live = model(frame, show=False, verbose=False)
    for result in results_live:
        for box in result.boxes:
            class_id = int(box.cls[0])
            label = model.names[class_id]
            conf = float(box.conf[0])
            
            if label != "person" and conf > 0.40:
                box_coords = box.xyxy[0].cpu().numpy().astype(int)
                current_frame_objects.append((label, conf, box_coords))

    for label, conf, coords in current_frame_objects:
        ten_tieng_viet = label
        color = (0, 255, 0)
        
        if label in ["Glass", "glass"]:
            ten_tieng_viet = "THUY TINH"
            color = (0, 255, 255)
        elif label in ["METAL", "Metal"]:
            ten_tieng_viet = "KIM LOAI"
            color = (0, 165, 255)
        elif label == "can":
            ten_tieng_viet = "VO LON"
            color = (255, 100, 0)
        elif label == "plastic":
            ten_tieng_viet = "NHUA"
            color = (0, 255, 0)
            
        cv2.rectangle(annotated_frame, (coords[0], coords[1]), (coords[2], coords[3]), color, 2)
        cv2.putText(annotated_frame, f"{ten_tieng_viet} {conf*100:.1f}%", (coords[0], coords[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    cv2.imshow(win_name, annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
if ser:
    ser.close()
print("Hệ thống đóng an toàn!")