# Comic Translator MVP
<img width="1919" height="1079" alt="Screenshot_1" src="https://github.com/user-attachments/assets/f95b1c2a-4dcc-4049-a4eb-9d3aebdb7c3b" />


Ứng dụng dịch truyện tranh tự động và chỉnh sửa bản dịch trực quan dạng giao diện desktop, phát triển bằng Python và PySide6. Ứng dụng hỗ trợ nhận dạng chữ (OCR), dịch tự động, chỉnh sửa nội dung dịch, căn chỉnh font chữ và kết xuất lại thành tệp truyện dịch hoàn chỉnh.

---

## 🚀 Các chức năng chính

### 1. Quản lý truyện và trang (CBZ / Ảnh đơn)
- **Hỗ trợ CBZ/ZIP**: Mở và giải nén tệp truyện định dạng `.cbz` hoặc `.zip`, tự động sinh danh sách ảnh thu nhỏ (thumbnails) để tiện theo dõi.
- **Tải/Lưu tiến trình (Save/Load Project)**: Lưu toàn bộ trạng thái dự án truyện đang dịch dở dang dưới dạng tệp `project.json`.
- **Tải/Lưu trang riêng lẻ (Save/Load Page)**: Lưu trữ hoặc khôi phục tọa độ chữ và bản dịch cho một trang cụ thể (dưới dạng tệp `{số_trang}.json`).
- **Tự động tải trang lưu**: Khi bạn chuyển đến một trang truyện đã có file `.json` tương ứng trong thư mục truyện, ứng dụng tự động nạp lại vùng chọn và bản dịch mà không cần thao tác thủ công.

### 2. Phát hiện và dịch văn bản (OCR & Translate)
- **Nhận dạng văn bản tự động (OCR)**: Sử dụng các thư viện AI mạnh mẽ (PaddleOCR / EasyOCR) để quét vị trí các bong bóng thoại và trích xuất chữ gốc tiếng Anh/ngôn ngữ nguồn.
- **Dịch tự động**: Tích hợp công cụ dịch để chuyển ngữ văn bản được chọn sang Tiếng Việt ngay lập tức.
- **Gộp bong bóng thoại (Merge Selected)**: Cho phép chọn nhiều vùng chữ rời rạc và gộp chúng lại thành một khối văn bản duy nhất để dịch trơn tru hơn.

### 3. Biên tập và kết xuất ảnh dịch trực quan
- **Thay đổi định dạng font chữ**: Hỗ trợ căn chỉnh cỡ chữ, chọn phông chữ và đổi màu sắc chữ dịch trực tiếp trên khung xem ảnh.
- **Bật/Tắt bong bóng thoại**: Cho phép tắt bớt các khối nhận diện sai, vẽ đè khung nền trắng xóa chữ gốc để hiển thị chữ dịch đè lên đẹp mắt.
- **Xuất tệp truyện dịch (Save CBZ)**: Lưu toàn bộ truyện đã dịch thành một file `.cbz` hoặc `.zip` mới với chữ dịch được vẽ đè lên trang truyện gốc một cách hoàn chỉnh.

---

## 🛠 Yêu cầu hệ thống và Cài đặt

Ứng dụng yêu cầu máy tính đã cài đặt sẵn **Python 3.8** trở lên.

### Các bước cài đặt:

1. **Tải mã nguồn ứng dụng về máy tính.**

2. **Tạo môi trường ảo Python (Virtual Environment) và kích hoạt nó:**
   ```bash
   # Tạo môi trường ảo .venv
   python -m venv .venv

   # Kích hoạt trên Windows (Command Prompt)
   .venv\Scripts\activate.bat

   # Kích hoạt trên Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   ```

3. **Cài đặt các thư viện phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```
   *Lưu ý: Nếu bạn muốn sử dụng PaddleOCR và PaddlePaddle tốt hơn trên GPU, hãy tham khảo tài liệu của Paddle để cài đặt phiên bản phù hợp.*

---

## 💻 Hướng dẫn sử dụng nhanh

1. **Khởi chạy ứng dụng:**
   ```bash
   python main.py
   ```

2. **Mở truyện dịch:**
   - Click nút **Open CBZ** để chọn tệp truyện `.cbz` mong muốn. 
   - Hoặc click **Open Image** để chọn một trang ảnh đơn lẻ.

3. **Thao tác dịch:**
   - Chọn trang truyện cần dịch từ danh sách thumbnail bên trái.
   - Click nút **Detect** để quét tự động tất cả các bong bóng thoại chứa chữ trên trang.
   - Các vùng chữ phát hiện được sẽ hiển thị ở cột bên phải. Bạn chọn vùng chữ, click **Translate** để dịch tự động, hoặc nhập trực tiếp bản dịch tự tay vào hộp thoại phía dưới.
   - Click **Save Page** để lưu trữ tiến trình dịch của trang đó (Ví dụ: `4.json` cho trang 4).
   - Click **Save Project** để lưu trạng thái của cả quyển truyện dở dang.

4. **Kết xuất truyện:**
   - Click **Save CBZ** để đóng gói toàn bộ trang truyện đã hoàn thành bản dịch thành một tệp CBZ mới để đọc.
