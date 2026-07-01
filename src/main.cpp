/**
 * MA NGUON ESP32 - THUNG RAC TU DONG KICH HOAT CAMERA CHO 10CM
 */

#include <ESP32Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- DINH NGHIA PIN DIEU KHIEN ---
const int TRIG_PIN = 5;         
const int ECHO_PIN = 18;        
const int SERVO_PIN = 13;       
const int LED_STATUS_PIN = 2;   

Servo myServo;
LiquidCrystal_I2C lcd(0x27, 16, 2); 

unsigned long lastSensorTime = 0;
const unsigned long sensorInterval = 200; // Tăng tốc độ quét cảm biến lên 200ms/lần

long measureDistance();
void executeSorting(int angle, String label);

void setup() {
  Serial.begin(115200);
  
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_STATUS_PIN, OUTPUT);
  digitalWrite(LED_STATUS_PIN, HIGH); 

  Wire.begin(21, 22); 
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("SYSTEM READY");
  lcd.setCursor(0, 1);
  lcd.print("Distance Mode");

  myServo.attach(SERVO_PIN);
  myServo.write(0); 
  delay(1000);
}

void loop() {
  if (millis() - lastSensorTime >= sensorInterval) {
    lastSensorTime = millis();
    long distance = measureDistance();
    
    // Cập nhật khoảng cách lên LCD
    lcd.setCursor(0, 1);
    lcd.print("Dist: " + String(distance) + " cm    "); 
    
    // NẾU CẢM BIẾN NHẬN ĐƯỢC VẬT TRONG KHOẢNG 10CM
    if (distance > 0 && distance <= 10) {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("OBJECT DETECTED");
      lcd.setCursor(0, 1);
      lcd.print("Waiting AI...");
      
      // Gửi tín hiệu kích hoạt lên Camera Laptop qua cổng USB
      Serial.println("DETECTED");
      
      // Bật chế độ "Đợi phản hồi từ máy tính" (Chờ tối đa 4 giây)
      unsigned long startWait = millis();
      bool receivedCommand = false;
      
      while (millis() - startWait < 10000) {
        if (Serial.available() > 0) {
          char cmd = Serial.read(); // Đọc ký tự phân loại gửi về từ Python
          
          if (cmd == '1') {
            executeSorting(45, "RAC TAI CHE"); // Quay 45 độ cho rác tái chế
            receivedCommand = true;
            break;
          }
          else if (cmd == '2') {
            executeSorting(90, "RAC HUU CO");  // Quay 90 độ cho rác hữu cơ
            receivedCommand = true;
            break;
          }
          else if (cmd == '3') {
            executeSorting(135, "RAC VO CO");  // Quay 135 độ cho rác vô cơ
            receivedCommand = true;
            break;
          }
        }
      }
      
      // Nếu quá thời gian chờ mà máy tính không phản hồi
      if (!receivedCommand) {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("AI TIMEOUT!");
        delay(1500);
      }
      
      // Trả lại giao diện sẵn sàng
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("SYSTEM READY");
    }
  }
}

// Hàm thực hiện quay servo phân loại, giữ nắp và đóng lại
void executeSorting(int angle, String label) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(label);
  lcd.setCursor(0, 1);
  lcd.print("Opening: " + String(angle) + " deg");
  
  myServo.write(angle); // Quay servo mở nắp ngăn tương ứng
  delay(5000);          // Giữ nắp mở trong 5 giây để bỏ rác
  
  myServo.write(0);     // Đóng nắp về vị trí 0 ban đầu
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("CLOSING LID...");
  delay(1000);          // Chờ servo đóng hoàn toàn
}

long measureDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 20000); // Giới hạn thời gian chờ cảm biến
  if (duration == 0) return 999;
  return duration * 0.034 / 2;
}